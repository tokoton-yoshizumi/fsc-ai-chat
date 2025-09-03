document.addEventListener("DOMContentLoaded", () => {
  // 最初のメッセージを表示
  addMessage(
    "こんにちは🌟 FSC AIです！😊<br>ご希望のサポートをお選びください✨",
    "FSC AI",
    true
  );
  // 最初の選択肢ボタンを表示
  showInitialChoices();
  // フォームの送信イベントを監視
  document
    .getElementById("chat-form")
    .addEventListener("submit", handleFormSubmit);
});

// チャットをリセットする関数
function resetChat() {
  const messageContainer = document.querySelector(".chat-messages");
  messageContainer.innerHTML = ""; // メッセージを全消去
  addMessage(
    "こんにちは🌟 FSC AIです！😊<br>ご希望のサポートをお選びください✨",
    "FSC AI",
    true
  );
  showInitialChoices();
  // 入力欄を有効化し、プレースホルダーを元に戻す
  const userInputElement = document.getElementById("user_input");
  userInputElement.placeholder = "メッセージを入力...";
  userInputElement.disabled = false;
}

// 1. 最初の選択肢ボタンを表示する関数
function showInitialChoices() {
  const choices = [
    { text: "📦 製品について", action: switchToFreeTextMode }, // ★ここを変更
    {
      text: "🛍️ 製品のご注文",
      action: () =>
        showLinkMessage(
          "ご注文はこちらのページからどうぞ🛒",
          "https://fujiwarasangyo.jp/order/"
        ),
    },
    {
      text: "🛠️ 校正・修理のご依頼",
      action: () =>
        showLinkMessage(
          "校正・修理のご依頼はこちらからどうぞ🔧",
          "https://fujiwarasangyo.jp/calibratio-repair/"
        ),
    },
    {
      text: "📩 お問い合わせ",
      action: () =>
        showLinkMessage(
          "お問い合わせはこちらのフォームをご利用ください📩",
          "https://fujiwarasangyo.jp/form-contact/"
        ),
    },
  ];

  const choiceContainer = createChoiceButtons(choices);
  document.querySelector(".chat-messages").appendChild(choiceContainer);
  scrollToBottom();
}

// 2. 「製品について」が押されたときに、自由入力モードに切り替える新しい関数
function switchToFreeTextMode() {
  addMessage(
    "製品についてですね！<br>どのようなことに関心がありますか？ご自由に質問を入力してください✍️",
    "FSC AI",
    true
  );

  // 入力欄のプレースホルダーを変更して、ユーザー入力を促す
  const userInputElement = document.getElementById("user_input");
  userInputElement.placeholder = "製品に関するご質問を入力...";
  userInputElement.focus(); // 入力欄にフォーカスを当てる
}

// 3. フォームが送信されたときのメインの処理
async function handleFormSubmit(event) {
  event.preventDefault();
  const userInputElement = document.getElementById("user_input");
  const userInput = userInputElement.value.trim();

  if (!userInput) return;

  addMessage(userInput, "ユーザー", false);
  userInputElement.value = "";

  try {
    showLoadingMessage();

    const response = await fetch("/ask", {
      // 修正済みの /ask APIを呼び出す
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userInput }),
    });

    const data = await response.json();
    removeLoadingMessage();

    let botResponseHTML = data.bot_response.replace(/\n/g, "<br>"); // 改行を<br>に変換

    // 回答のソース元リンクがあれば表示
    if (data.sources && data.sources.length > 0) {
      botResponseHTML += '<div class="sources">関連ページ:<ul>';
      data.sources.forEach((source) => {
        // URLの代わりにタイトルを表示し、URLをリンク先にする
        botResponseHTML += `<li><a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a></li>`;
      });
      botResponseHTML += "</ul></div>";
    }

    addMessage(botResponseHTML, "FSC AI", true);
  } catch (error) {
    console.error("Error:", error);
    removeLoadingMessage();
    addMessage(
      "エラーが発生しました。もう一度お試しください。",
      "FSC AI",
      true
    );
  }
}

// --- 以下はメッセージ表示などの補助的な関数群です ---

// 選択肢ボタンを生成する補助関数
function createChoiceButtons(choices) {
  const container = document.createElement("div");
  container.classList.add("choices");

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.innerHTML = choice.text;
    button.classList.add("choice-button");
    button.onclick = () => {
      addMessage(button.innerText, "ユーザー", false); // ユーザーがボタンを押したことを表示
      choice.action();
      // 押されたボタンは再度押せないように非表示にする
      container.style.display = "none";
    };
    container.appendChild(button);
  });
  return container;
}

// リンク付きのメッセージを表示する補助関数
function showLinkMessage(message, link) {
  const content =
    message +
    `<br><button class="link-button" onclick="window.open('${link}', '_blank')">リンクへ移動</button>`;
  addMessage(content, "FSC AI", true);
}

// メッセージをチャット欄に追加する汎用関数
function addMessage(content, sender, isAI) {
  const messageContainer = document.querySelector(".chat-messages");
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", isAI ? "received" : "sent");

  let innerHTML = "";
  if (isAI) {
    innerHTML += `<img src="/static/images/icon.png" class="message-icon" alt="AI Icon">`;
  }
  innerHTML += `<div class="message-text"><p>${content}</p><p class="time">${sender}</p></div>`;

  messageDiv.innerHTML = innerHTML;
  messageContainer.appendChild(messageDiv);
  scrollToBottom();
}

// ローディング表示関連
let loadingMessageElement = null;
function showLoadingMessage() {
  const messageContainer = document.querySelector(".chat-messages");
  loadingMessageElement = document.createElement("div");
  loadingMessageElement.classList.add("message", "sent");
  loadingMessageElement.innerHTML = `
        <img src="/static/images/icon.png" class="message-icon" alt="AI Icon">
        <div class="message-text">
            <p>🧠 回答を考えています...</p>
            <p class="time">FSC AI</p>
        </div>
    `;
  messageContainer.appendChild(loadingMessageElement);
  scrollToBottom();
}

function removeLoadingMessage() {
  if (loadingMessageElement) {
    loadingMessageElement.remove();
    loadingMessageElement = null;
  }
}

// 自動で最下部にスクロールする関数
function scrollToBottom() {
  const container = document.querySelector(".chat-messages");
  container.scrollTop = container.scrollHeight;
}
