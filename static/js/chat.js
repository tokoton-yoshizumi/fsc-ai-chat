document.addEventListener("DOMContentLoaded", () => {
  addMessageWithIcon(
    "こんにちは🌟 FSC AIです！😊<br>ご希望のサポートをお選びください✨",
    "FSC AI",
    "sent",
    true
  );
  showInitialChoices();
});

// チャットをリセットして初期状態に戻す関数
function resetChat() {
  const messageContainer = document.querySelector(".chat-messages");
  messageContainer.innerHTML = ""; // 全メッセージクリア
  addMessageWithIcon(
    "こんにちは🌟 FSC AIです！😊<br>ご希望のサポートをお選びください✨",
    "FSC AI",
    "sent",
    true
  );
  showInitialChoices();
}

// **起動時の選択肢を表示**
function showInitialChoices() {
  const messageContainer = document.querySelector(".chat-messages");
  const choiceContainer = document.createElement("div");
  choiceContainer.classList.add("choices");

  const choices = [
    { text: "📦 製品について", action: askForProductName },
    { text: "🛍️ 製品のご注文", action: askOrderOptions },
    { text: "🛠️ 校正・修理のご依頼", action: askCalibrationRepair },
    { text: "📩 お問い合わせ", action: askContactForm },
  ];

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.textContent = choice.text;
    button.classList.add("choice-button");
    button.onclick = () => {
      addMessageWithIcon(choice.text, "ユーザー", "received", false);
      choice.action();
    };
    choiceContainer.appendChild(button);
  });

  messageContainer.appendChild(choiceContainer);
  messageContainer.scrollTop = messageContainer.scrollHeight;
}

// **「📦 製品について」→ フォームのプレースホルダーを変更**
function askForProductName() {
  addMessageWithIcon(
    "どの製品について知りたいですか？🔍<br>製品名を入力してください💬😊",
    "FSC AI",
    "sent",
    true
  );

  const userInputElement = document.getElementById("user_input");
  userInputElement.placeholder = "製品名を入力してください";
  userInputElement.dataset.inputType = "product"; // 製品モードを判別
}

// **「🛍️ ご注文」→ ご注文の選択肢を表示**
function askOrderOptions() {
  addMessageWithIcon("ご注文内容を選択してください🛒", "FSC AI", "sent", true);
  const messageContainer = document.querySelector(".chat-messages");
  const choiceContainer = document.createElement("div");
  choiceContainer.classList.add("choices");

  const choices = [
    { text: "購入商品のご注文", link: "https://fujiwarasangyo.jp/order/" },
    {
      text: "一般商品のレンタル",
      link: "https://fujiwarasangyo.jp/form-rental/",
    },
    {
      text: "ロックボルト試験器具関連のレンタル",
      link: "https://fujiwarasangyo.jp/rockbolt-form/",
    },
  ];

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.textContent = choice.text;
    button.classList.add("choice-button");
    button.onclick = () => {
      addMessageWithIcon(choice.text, "ユーザー", "received", false);
      showLinkMessage("こちらのリンクをご確認ください👇", choice.link);
    };
    choiceContainer.appendChild(button);
  });

  messageContainer.appendChild(choiceContainer);
  messageContainer.scrollTop = messageContainer.scrollHeight;
}

// **「🛠️ 校正・修理」→ 校正・修理のリンクを案内**
function askCalibrationRepair() {
  showLinkMessage(
    "校正・修理のご依頼はこちらのフォームからどうぞ🔧",
    "https://fujiwarasangyo.jp/calibratio-repair/"
  );
}

// **「📩 お問い合わせ」→ お問い合わせフォームのリンクを案内**
function askContactForm() {
  showLinkMessage(
    "お問い合わせはこちらのフォームをご利用ください📩",
    "https://fujiwarasangyo.jp/form-contact/"
  );
}

// ユーザーにリンクを案内するメッセージを表示する共通関数（ボタン表示版）
function showLinkMessage(message, link) {
  const content =
    message +
    `<br><button class="link-button" onclick="window.open('${link}', '_blank')">リンクへ移動</button>`;
  addMessageWithIcon(content, "FSC AI", "sent", true);
}

// **製品名送信後、見出しリストを取得**
async function processProductName(event) {
  event.preventDefault(); // ページリロードを防ぐ

  const userInputElement = document.getElementById("user_input");
  const userInput = userInputElement.value.trim();

  if (!userInput) return;

  if (userInputElement.dataset.inputType === "product") {
    addMessageWithIcon(userInput, "ユーザー", "received", false);

    try {
      const response = await fetch("/get_product_info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: userInput }),
      });

      const data = await response.json();

      if (data.choices && data.choices.length > 0) {
        addMessageWithIcon(
          `「${userInput}」についてですね！😊\n知りたい項目を選んでください✨`,
          "FSC AI",
          "sent",
          true
        );

        // **見出しの選択肢を表示**
        showSubChoices(
          data.choices,
          "以下の見出しから選んでください🔽",
          data.source_url
        );
      } else {
        addMessageWithIcon(
          "該当する製品ページが見つかりませんでした😢",
          "FSC AI",
          "sent",
          true
        );
      }
    } catch (error) {
      console.error("Error fetching product info:", error);
      addMessageWithIcon(
        "エラーが発生しました😓。もう一度お試しください。",
        "FSC AI",
        "sent",
        true
      );
    }
  }
}

// **h2 を選択した後、質問入力モードにする**
function handleHeadingSelection(url, heading) {
  console.log("🔹 選択された見出し:", heading);
  addMessageWithIcon(
    `「${heading}」について知りたい😃`,
    "ユーザー",
    "received",
    false
  );

  const userInputElement = document.getElementById("user_input");
  userInputElement.placeholder = `「${heading}」について質問を入力✍️`;
  userInputElement.dataset.inputType = "question";
  userInputElement.dataset.url = url;
  userInputElement.dataset.heading = heading;

  addMessageWithIcon(
    `「${heading}」についてですね！💡\nどのようなご質問がありますか？🤔`,
    "FSC AI",
    "sent",
    true
  );
}

// **選択肢を表示する汎用関数**
function showSubChoices(choices, promptText, url) {
  addMessageWithIcon(promptText, "FSC AI", "sent", true);

  const messageContainer = document.querySelector(".chat-messages");
  const choiceContainer = document.createElement("div");
  choiceContainer.classList.add("choices");

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.textContent = choice;
    button.classList.add("choice-button");

    button.onclick = () => {
      console.log("ボタンがクリックされました:", choice);
      handleHeadingSelection(url, choice);
    };

    choiceContainer.appendChild(button);
  });

  messageContainer.appendChild(choiceContainer);
  messageContainer.scrollTop = messageContainer.scrollHeight;
}

// **フォーム送信時の処理**
async function processUserInput(event) {
  event.preventDefault();

  const userInputElement = document.getElementById("user_input");
  const userInput = userInputElement.value.trim();

  if (!userInput) return;

  if (userInputElement.dataset.inputType === "question") {
    addMessageWithIcon(userInput, "ユーザー", "received", false);

    try {
      const response = await fetch("/get_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: userInputElement.dataset.url,
          heading: userInputElement.dataset.heading,
          question: userInput,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTPエラー: ${response.status}`);
      }

      const data = await response.json();
      addMessageWithIcon(data.bot_response, "FSC AI", "sent", true);

      if (data.show_contact) {
        askContactOptions();
      }
    } catch (error) {
      console.error("❌ fetchエラー:", error);
      addMessageWithIcon(
        "エラーが発生しました😓。もう一度お試しください。",
        "FSC AI",
        "sent",
        true
      );
    }

    userInputElement.value = "";
  }
}

// **フォームの送信イベントを監視**
document
  .getElementById("chat-form")
  .addEventListener("submit", processUserInput);

// **メッセージを追加する関数（AI のみアイコン付き）**
function addMessageWithIcon(content, sender, className, isAI) {
  const messageContainer = document.querySelector(".chat-messages");
  const message = document.createElement("div");
  message.classList.add("message", className);

  if (isAI) {
    const icon = document.createElement("img");
    icon.src = "/static/images/icon.png";
    icon.classList.add("message-icon");
    message.appendChild(icon);
  }

  const textWrapper = document.createElement("div");
  textWrapper.classList.add("message-text");
  textWrapper.innerHTML = `<p>${content}</p><p class="time">${sender}</p>`;

  message.appendChild(textWrapper);
  messageContainer.appendChild(message);

  messageContainer.scrollTop = messageContainer.scrollHeight;
}
