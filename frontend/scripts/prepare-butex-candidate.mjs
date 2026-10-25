import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const lock = JSON.parse(readFileSync(new URL("../butex-candidate.lock.json", import.meta.url), "utf8"));
const token = process.env.GITLAB_BUTEX_READ_TOKEN?.trim();
if (!token) {
  console.error("BLOCKED: Private BuTeX candidate requires GitHub Actions secret GITLAB_BUTEX_READ_TOKEN (GitLab read_api scope). Do not fall back to the published 7.4.x package.");
  process.exit(2);
}
const root = `https://gitlab.com/api/v4/projects/${lock.gitlab_project_id}`;
const headers = { "PRIVATE-TOKEN": token };
async function download(path) {
  const response = await fetch(root + path, { headers, signal: AbortSignal.timeout(90000) });
  if (!response.ok) throw new Error(`BuTeX candidate artifact request failed (HTTP ${response.status}); check GitLab read_api permission and exact job id.`);
  return Buffer.from(await response.arrayBuffer());
}
try {
  const job = JSON.parse((await download(`/jobs/${lock.gitlab_job_id}`)).toString("utf8"));
  if (job.id !== lock.gitlab_job_id || job.status !== "success" ||
      job.commit?.id !== lock.gitlab_commit || job.pipeline?.id !== lock.gitlab_pipeline_id) {
    throw new Error("BuTeX candidate job does not match pinned successful commit/pipeline.");
  }
  const prefix = `/jobs/${lock.gitlab_job_id}/artifacts/artifacts/`;
  const archive = await download(prefix + "butex-candidate.tgz");
  const checksumFile = (await download(prefix + "butex-candidate.sha256")).toString("utf8");
  const checksumParts = checksumFile.trim().split("  ");
  if (checksumParts.length !== 2 || checksumParts[1] !== "artifacts/butex-candidate.tgz") {
    throw new Error("BuTeX CI checksum manifest format is invalid.");
  }
  const publishedHash = checksumParts[0];
  const actualHash = createHash("sha256").update(archive).digest("hex");
  if (publishedHash !== lock.tarball_sha256 || actualHash !== lock.tarball_sha256) {
    throw new Error("BuTeX tarball SHA-256 mismatches GitLab CI artifact or pinned lock; refusing install.");
  }
  const directory = fileURLToPath(new URL("../.candidate/", import.meta.url));
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, "butex-candidate.tgz"), archive);
  writeFileSync(join(directory, "provenance.json"), JSON.stringify({
    source_commit: lock.gitlab_commit, pipeline_id: lock.gitlab_pipeline_id,
    job_id: lock.gitlab_job_id, sha256: actualHash, verified: true,
  }, null, 2) + "\n");
  console.log(`Attested unpublished BuTeX candidate: ${lock.gitlab_commit.slice(0, 12)} / job ${lock.gitlab_job_id} / sha256 ${actualHash}`);
} catch (error) {
  console.error("BLOCKED: Could not verify the private BuTeX candidate:", error instanceof Error ? error.message : String(error));
  process.exitCode = 2;
}
