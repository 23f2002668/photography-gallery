document.addEventListener("DOMContentLoaded", () => {
    const introOverlay = document.getElementById("intro-overlay");
    if (introOverlay) { setTimeout(() => { introOverlay.classList.add("dissolve-splash-screen"); }, 2200); }
    armMediaExtractionLocks();
});

function armMediaExtractionLocks() {
    document.addEventListener("contextmenu", (e) => { if (e.target.tagName === "IMG") { e.preventDefault(); alert("Right-click disabled on images."); } });
    window.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && ["s", "S", "u", "U"].includes(e.key)) { e.preventDefault(); alert("Save shortcuts disabled."); } });
}