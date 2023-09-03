$(function () {
  if (
    location.pathname == "/login" &&
    !location.search &&
    !localStorage.getItem("session_last_route")
  ) {
    const url = new URL(window.location);
    url.searchParams.set("redirect-to", "/drive/home");
    window.history.pushState({}, "", url);
  }
});
