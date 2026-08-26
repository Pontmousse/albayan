import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  "/al-idayat(.*)",
  "/maktabi(.*)",
  "/daawa(.*)",
  "/admin(.*)",
  "/oauth-consent(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    const unauthenticatedUrl = new URL("/tawajjuh", req.url);
    const path = req.nextUrl.pathname;
    if (path.startsWith("/daawa") || path.startsWith("/oauth-consent")) {
      unauthenticatedUrl.searchParams.set(
        "next",
        `${path}${req.nextUrl.search}`,
      );
    }
    await auth.protect({
      unauthenticatedUrl: unauthenticatedUrl.toString(),
    });
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
