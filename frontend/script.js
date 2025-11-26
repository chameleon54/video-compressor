const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const startBtn = document.getElementById("start-btn");

let selectedFiles = [];

dropZone.onclick = () => fileInput.click();

fileInput.onchange = (e) => {
    addFiles([...e.target.files]);
};

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.background = "#eee";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.background = "";
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.background = "";
    addFiles([...e.dataTransfer.files]);
});


function addFiles(files) {
    files.forEach(file => {
        selectedFiles.push(file);

        const container = document.createElement("div");
        container.classList.add("file-item");

        const videoPreview = document.createElement("video");
        videoPreview.classList.add("thumbnail");
        videoPreview.src = URL.createObjectURL(file);
        videoPreview.muted = true;
        videoPreview.autoplay = true;

        const name = document.createElement("p");
        name.textContent = file.name;

        const progressBarContainer = document.createElement("div");
        progressBarContainer.classList.add("progress-container");

        const progressBar = document.createElement("div");
        progressBar.classList.add("progress-bar");

        progressBarContainer.appendChild(progressBar);

        container.appendChild(videoPreview);
        container.appendChild(name);
        container.appendChild(progressBarContainer);

        fileList.appendChild(container);

        file.progressBar = progressBar;
    });
}


startBtn.onclick = async () => {
    if (selectedFiles.length === 0) {
        alert("No videos selected.");
        return;
    }

    const form = new FormData();
    selectedFiles.forEach(f => form.append("videos", f));

    form.append("crf", document.getElementById("crf").value);
    form.append("threads", document.getElementById("threads").value);

    const res = await fetch("http://localhost:5000/compress", {
        method: "POST",
        body: form
    });

    const tasks = await res.json();

    tasks.forEach((task, index) => trackProgress(task.id, selectedFiles[index]));
};


async function trackProgress(id, file) {
    const interval = setInterval(async () => {
        const res = await fetch(`http://localhost:5000/progress/${id}`);
        const data = await res.json();

        if (data.progress >= 1) {
            file.progressBar.style.width = "100%";
            clearInterval(interval);

            downloadFile(id);
        } else {
            file.progressBar.style.width = (data.progress * 100) + "%";
        }
    }, 500);
}

function downloadFile(id) {
    const a = document.createElement("a");
    a.href = `http://localhost:5000/download/${id}`;
    a.download = "compressed.mp4";
    a.click();
}
