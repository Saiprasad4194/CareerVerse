// =====================================================
// CareerVerse AI — Executive AI Career Mentor Chat Logic
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("sendBtn");
    const userInput = document.getElementById("userMessage");
    const chatBox = document.getElementById("chatBox");
    const welcomeScreen = document.getElementById("welcomeScreen");
    const newChatBtn = document.getElementById("newChatBtn");
    const clearChatBtn = document.getElementById("clearChatBtn");
    const copyChatBtn = document.getElementById("copyChatBtn");
    const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
    const chatSidebar = document.getElementById("chatSidebar");

    let isThinking = false;

    // -----------------------------------------------------
    // Auto-Expand Textarea
    // -----------------------------------------------------
    if (userInput) {
        userInput.addEventListener("input", function () {
            this.style.height = "auto";
            this.style.height = (this.scrollHeight) + "px";
        });

        userInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // -----------------------------------------------------
    // Send Button & Listeners
    // -----------------------------------------------------
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }

    // Sidebar Toggle
    if (toggleSidebarBtn && chatSidebar) {
        toggleSidebarBtn.addEventListener("click", () => {
            chatSidebar.classList.toggle("collapsed");
        });
    }

    // Suggestion Cards Click
    document.querySelectorAll(".suggestion-card, .topic-chip, .pill-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const prompt = this.getAttribute("data-prompt") || this.innerText;
            if (prompt && userInput) {
                userInput.value = prompt;
                sendMessage();
            }
        });
    });

    // Clear Chat Button
    if (clearChatBtn) {
        clearChatBtn.addEventListener("click", async () => {
            if (confirm("Are you sure you want to clear this conversation?")) {
                chatBox.innerHTML = `
                    <div id="welcomeScreen" class="welcome-screen">
                        <div class="welcome-badge"><i class="fa-solid fa-wand-magic-sparkles"></i> AI CAREER MENTOR</div>
                        <h1>Where would you like to take your <span class="gradient-text">Career today?</span></h1>
                        <p>Ask anything about tech roles, skill roadmaps, interview strategies, or global pay bands.</p>
                    </div>
                `;
                try {
                    await fetch("/clear-chat", { method: "POST" });
                } catch (e) {
                    console.error(e);
                }
            }
        });
    }

    // Robust Cross-Browser & Cross-Protocol Copy Helper (Supports HTTP, HTTPS, & Mobile)
    function copyToClipboard(textToCopy) {
        if (!textToCopy) return Promise.reject("Nothing to copy");
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(textToCopy);
        } else {
            return new Promise((resolve, reject) => {
                try {
                    const textArea = document.createElement("textarea");
                    textArea.value = textToCopy;
                    textArea.style.position = "fixed";
                    textArea.style.left = "-999999px";
                    textArea.style.top = "-999999px";
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    const successful = document.execCommand("copy");
                    document.body.removeChild(textArea);
                    if (successful) {
                        resolve();
                    } else {
                        reject(new Error("execCommand copy failed"));
                    }
                } catch (err) {
                    reject(err);
                }
            });
        }
    }

    // Copy Session Transcript
    if (copyChatBtn) {
        copyChatBtn.addEventListener("click", () => {
            const text = chatBox.innerText;
            copyToClipboard(text).then(() => {
                alert("Conversation transcript copied to clipboard!");
            }).catch(err => {
                console.error("Copy failed:", err);
                alert("Could not copy transcript automatically. Please select text manually.");
            });
        });
    }

    // New Chat Button
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            chatBox.innerHTML = `
                <div id="welcomeScreen" class="welcome-screen">
                    <div class="welcome-badge"><i class="fa-solid fa-wand-magic-sparkles"></i> AI CAREER MENTOR</div>
                    <h1>Where would you like to take your <span class="gradient-text">Career today?</span></h1>
                    <p>Ask anything about tech roles, skill roadmaps, interview strategies, or global pay bands.</p>
                </div>
            `;
            fetch("/clear-chat", { method: "POST" }).catch(err => console.error(err));
        });
    }

    // -----------------------------------------------------
    // Send Message Handler
    // -----------------------------------------------------
    async function sendMessage() {
        if (!userInput || isThinking) return;

        const message = userInput.value.trim();
        if (message === "") return;

        // Hide welcome screen on first prompt
        const currentWelcome = document.getElementById("welcomeScreen");
        if (currentWelcome) {
            currentWelcome.remove();
        }

        // 1. Append User Message
        appendUserMessage(message);

        userInput.value = "";
        userInput.style.height = "auto";
        chatBox.scrollTop = chatBox.scrollHeight;

        // 2. Append AI Typing Indicator
        isThinking = true;
        const loaderId = appendTypingIndicator();
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const response = await fetch("/career-chat-api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();
            removeTypingIndicator(loaderId);
            isThinking = false;

            if (data.success === false) {
                appendAIMessage("⚠️ " + (data.error || "Unable to get career guidance. Please try again."));
            } else {
                const answerText = data.data?.answer || data.answer || "No response received.";
                appendAIMessage(answerText);
            }
        } catch (error) {
            console.error(error);
            removeTypingIndicator(loaderId);
            isThinking = false;
            appendAIMessage("❌ Network error connecting with CareerVerse AI. Please check your connection.");
        }

        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // -----------------------------------------------------
    // DOM Appenders
    // -----------------------------------------------------
    function appendUserMessage(text) {
        const msgRow = document.createElement("div");
        msgRow.className = "msg-row user-row";
        msgRow.innerHTML = `
            <div class="msg-avatar-icon"><i class="fa-solid fa-user"></i></div>
            <div class="msg-bubble">${escapeHtml(text)}</div>
        `;
        chatBox.appendChild(msgRow);
    }

    function appendTypingIndicator() {
        const id = "loader_" + Date.now();
        const loaderRow = document.createElement("div");
        loaderRow.className = "msg-row ai-row";
        loaderRow.id = id;
        loaderRow.innerHTML = `
            <div class="msg-avatar-icon"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-bubble">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatBox.appendChild(loaderRow);
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function appendAIMessage(rawText) {
        const msgRow = document.createElement("div");
        msgRow.className = "msg-row ai-row";

        const formattedContent = formatMarkdown(rawText);

        msgRow.innerHTML = `
            <div class="msg-avatar-icon"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-bubble">
                ${formattedContent}
                <div class="msg-actions">
                    <button class="msg-action-btn copy-msg-btn"><i class="fa-regular fa-copy"></i> Copy</button>
                </div>
            </div>
        `;

        chatBox.appendChild(msgRow);

        // Bind Copy Button
        const copyBtn = msgRow.querySelector(".copy-msg-btn");
        if (copyBtn) {
            copyBtn.addEventListener("click", function () {
                copyToClipboard(rawText).then(() => {
                    this.innerHTML = `<i class="fa-solid fa-check" style="color:#22c55e"></i> Copied!`;
                    setTimeout(() => {
                        this.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
                    }, 2000);
                }).catch(err => {
                    console.error("Copy failed:", err);
                    this.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color:#ef4444"></i> Failed`;
                    setTimeout(() => {
                        this.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
                    }, 2000);
                });
            });
        }
    }

    // Helper: HTML Escape
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.innerText = text;
        return div.innerHTML;
    }

    // Helper: Format Markdown
    function formatMarkdown(text) {
        if (!text) return "";

        let formatted = text
            // Headings
            .replace(/### (.*?)(\n|$)/g, "<h3>$1</h3>")
            .replace(/## (.*?)(\n|$)/g, "<h2>$1</h2>")
            .replace(/# (.*?)(\n|$)/g, "<h1>$1</h1>")
            // Bold
            .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
            // Inline Code
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            // Bullet list items
            .replace(/^\* (.*)$/gm, "<li>$1</li>")
            .replace(/^- (.*)$/gm, "<li>$1</li>")
            // Numbered list items
            .replace(/^\d+\.\s(.*)$/gm, "<li>$1</li>")
            // Paragraph breaks
            .replace(/\n/g, "<br>");

        return formatted;
    }
});