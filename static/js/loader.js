let loaderInterval;

const messages = [
    "🤖 AI is analyzing your request...",
    "📊 Gathering insights...",
    "🧠 Thinking intelligently...",
    "⚡ Preparing your report...",
    "🚀 Almost done..."
];

function showLoader(customMessage = null) {

    const loader = document.getElementById("loader");
    const text = document.getElementById("loaderText");

    loader.classList.add("active");

    let index = 0;

    text.innerHTML = customMessage || messages[0];

    if (!customMessage) {

        loaderInterval = setInterval(() => {

            index = (index + 1) % messages.length;

            text.innerHTML = messages[index];

        }, 1800);

    }

}

function hideLoader() {

    clearInterval(loaderInterval);

    document.getElementById("loader").classList.remove("active");

}