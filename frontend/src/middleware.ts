import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  "/al-idayat(.*)",
  "/maktabi(.*)",
  "/daawa(.*)",
  "/admin(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    const unauthenticatedUrl = new URL("/tawajjuh", req.url);
    if (req.nextUrl.pathname.startsWith("/daawa")) {
      unauthenticatedUrl.searchParams.set(
        "next",
        `${req.nextUrl.pathname}${req.nextUrl.search}`,
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
