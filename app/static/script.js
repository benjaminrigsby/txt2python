document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("copyBtn");
  const pre = document.getElementById("code");
  if (btn && pre) {
    btn.addEventListener("click", async () => {
      const text = pre.innerText || pre.textContent || "";
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = "Copy"), 1200);
      } catch (e) {
        console.error(e);
        btn.textContent = "Copy failed";
        setTimeout(() => (btn.textContent = "Copy"), 1500);
      }
    });
  }
});
