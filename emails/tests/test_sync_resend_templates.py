from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


EMAILS_DIR = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = EMAILS_DIR / "sync-resend-templates.sh"


class SyncResendTemplatesTests(unittest.TestCase):
    def test_declared_variables_are_passed_to_create_and_update(self) -> None:
        expected_vars = {
            "USER_NAME:string",
            "LOGIN_URL:string",
            "SITE_URL:string",
            "ASSET_BASE_URL:string",
        }

        for exists, operation in ((False, "create"), (True, "update")):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                bin_path = tmp_path / "bin"
                bin_path.mkdir()
                source = tmp_path / "Welcome.tsx"
                html = tmp_path / "Welcome.html"
                source.write_text("export default null;", encoding="utf-8")
                html.write_text("{{{USER_NAME}}}", encoding="utf-8")
                config = tmp_path / "templates.yaml"
                config.write_text(
                    textwrap.dedent(
                        f"""\
                        templates:
                          - alias: welcome-ar
                            name: Welcome
                            subject: Welcome
                            file: {source}
                            html_file: {html}
                            variables:
                              USER_NAME: string
                              LOGIN_URL: string
                              SITE_URL: string
                              ASSET_BASE_URL: string
                            publish: false
                        """
                    ),
                    encoding="utf-8",
                )

                self._write_fakes(bin_path)
                log = tmp_path / "resend.log"
                env = {
                    **os.environ,
                    "PATH": f"{bin_path}:{os.environ['PATH']}",
                    "RESEND_API_KEY": "re_test",
                    "RESEND_TEMPLATE_EXISTS": "1" if exists else "0",
                    "RESEND_LOG": str(log),
                }
                subprocess.run([SYNC_SCRIPT, config], check=True, env=env, capture_output=True)

                calls = [line.split("\0") for line in log.read_text().splitlines()]
                args = next(call for call in calls if call[:2] == ["templates", operation])
                actual_vars = {args[index + 1] for index, arg in enumerate(args) if arg == "--var"}
                self.assertEqual(actual_vars, expected_vars)
                self.assertIn("--html-file", args)

    @staticmethod
    def _write_fakes(bin_path: Path) -> None:
        (bin_path / "npm").write_text("#!/bin/sh\nexit 0\n")
        (bin_path / "resend").write_text(
            """#!/bin/bash
if [[ "$1 $2" == "templates get" ]]; then
  [[ "$RESEND_TEMPLATE_EXISTS" == 1 ]]
  exit
fi
printf '%s\\0' "$@" >> "$RESEND_LOG"
printf '\\n' >> "$RESEND_LOG"
"""
        )
        (bin_path / "yq").write_text(
            """#!/usr/bin/env python3
import re, sys, yaml
query, filename = sys.argv[-2:]
data = yaml.safe_load(open(filename, encoding='utf-8'))
if query == '.templates | length':
    print(len(data['templates'])); raise SystemExit
i = int(re.search(r'templates\\[(\\d+)\\]', query).group(1))
item = data['templates'][i]
if 'to_entries' in query:
    for key, value in item.get('variables', {}).items(): print(f'{key}:{value}')
else:
    key = query.rsplit('.', 1)[-1]
    value = item.get(key)
    print('null' if value is None else str(value).lower() if isinstance(value, bool) else value)
"""
        )
        for executable in bin_path.iterdir():
            executable.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
