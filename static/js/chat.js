(() => {
  "use strict";

  const app = document.getElementById("chatApp");
  if (!app) return;

  const translations = {
    en: {
      directory: "Service directory",
      directoryHelp: "Choose a topic to guide your question.",
      allServices: "All services",
      privacyTitle: "Privacy first",
      privacyText: "Do not enter passwords, NIN, BVN or bank details.",
      assistantName: "Nasarawa Assistant",
      ready: "Ready to help",
      clear: "Clear",
      welcomeKicker: "WELCOME · SANNU",
      welcomeTitle: "Find the right government service, faster.",
      welcomeText: "Ask in English or Hausa. I will answer only when the FAQ knowledge base has a reliable match.",
      popular: "Popular questions",
      noPublished: "Published suggestions will appear here.",
      inputLabel: "Ask a government service question",
      placeholder: "Ask about scholarships, healthcare, tax…",
      send: "Send",
      disclaimer: "Information only — not an application or payment portal.",
      howTitle: "How this assistant works",
      howOne: "Ask one clear service question.",
      howTwo: "The system checks published bilingual FAQs.",
      howThree: "Open the cited official source to continue.",
      accuracyTitle: "Accuracy before answers",
      accuracyText: "If no reliable answer is available, the assistant records the question for review instead of guessing.",
      humanHelp: "Need human help?",
      humanHelpText: "Use the verified government enquiry channel for a case-specific question.",
      officialContacts: "Official contacts",
      related: "Related questions",
      source: "Official source",
      verified: "Verified guidance",
      awaiting: "Awaiting official confirmation",
      helpful: "Was this helpful?",
      yes: "Yes",
      no: "Not quite",
      thanks: "Thank you for the feedback.",
      error: "The assistant is temporarily unavailable. Please try again.",
      clearConfirm: "Clear this conversation and start a new one?",
      redacted: "Sensitive-looking information was removed before your message was stored.",
    },
    ha: {
      directory: "Jerin ayyuka",
      directoryHelp: "Zaɓi batu domin jagorantar tambayarka.",
      allServices: "Dukkan ayyuka",
      privacyTitle: "Kiyaye sirrinka",
      privacyText: "Kada ka saka kalmar sirri, NIN, BVN ko bayanan banki.",
      assistantName: "Mai Taimakon Nasarawa",
      ready: "A shirye don taimako",
      clear: "Goge",
      welcomeKicker: "SANNU · WELCOME",
      welcomeTitle: "Samu aikin gwamnati cikin sauƙi.",
      welcomeText: "Yi tambaya da Hausa ko Turanci. Zan amsa ne kawai idan akwai tabbatacciyar amsa a kundin FAQ.",
      popular: "Tambayoyin da aka fi yi",
      noPublished: "Tambayoyin da aka wallafa za su bayyana a nan.",
      inputLabel: "Yi tambaya kan aikin gwamnati",
      placeholder: "Tambaya kan tallafin karatu, lafiya, haraji…",
      send: "Aika",
      disclaimer: "Bayani ne kawai — ba shafin neman aiki ko biyan kuɗi ba ne.",
      howTitle: "Yadda mai taimako ke aiki",
      howOne: "Yi tambaya ɗaya a sarari.",
      howTwo: "Tsarin yana duba FAQ da aka wallafa a harsuna biyu.",
      howThree: "Buɗe majiyar hukuma domin ci gaba.",
      accuracyTitle: "Inganci kafin amsa",
      accuracyText: "Idan babu tabbatacciyar amsa, ana ajiye tambayar domin dubawa maimakon yin zato.",
      humanHelp: "Kana buƙatar taimakon mutum?",
      humanHelpText: "Yi amfani da hanyar tuntuɓar gwamnati da aka tabbatar domin tambaya ta musamman.",
      officialContacts: "Tuntuɓar hukuma",
      related: "Tambayoyi masu alaƙa",
      source: "Majiyar hukuma",
      verified: "Bayanin da aka tabbatar",
      awaiting: "Ana jiran tabbacin hukuma",
      helpful: "Shin wannan ya taimaka?",
      yes: "Eh",
      no: "Ba sosai ba",
      thanks: "Mun gode da ra’ayinka.",
      error: "Mai taimako ba ya samuwa a yanzu. Ka sake gwadawa.",
      clearConfirm: "A goge wannan tattaunawa a fara sabuwa?",
      redacted: "An cire bayanan da suke kama da na sirri kafin a ajiye saƙonka.",
    },
  };

  const pane = document.getElementById("messagesPane");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const sendButton = document.getElementById("sendMessage");
  const typing = document.getElementById("typingIndicator");
  const clearButton = document.getElementById("clearChat");
  const redactionNotice = document.getElementById("redactionNotice");
  let language = localStorage.getItem("tambayi-language");
  let selectedCategory = "";
  let busy = false;

  const text = (key) => translations[language]?.[key] || translations.en[key] || key;

  function csrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function make(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  }

  function icon(name, className = "") {
    return make("i", `bi bi-${name}${className ? ` ${className}` : ""}`);
  }

  function currentTime(value = new Date()) {
    const date = value instanceof Date ? value : new Date(value);
    return new Intl.DateTimeFormat(language === "ha" ? "ha-NG" : "en-NG", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  function scrollToEnd() {
    pane.scrollTo({ top: pane.scrollHeight, behavior: "smooth" });
  }

  function applyLanguage(nextLanguage, persist = true) {
    language = nextLanguage === "ha" ? "ha" : "en";
    if (persist) localStorage.setItem("tambayi-language", language);
    document.documentElement.lang = language;
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      const value = text(element.dataset.i18n);
      if (value) element.textContent = value;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
      element.placeholder = text(element.dataset.i18nPlaceholder);
    });
    document.querySelectorAll("[data-language]").forEach((button) => {
      button.classList.toggle("active", button.dataset.language === language);
      button.setAttribute("aria-pressed", String(button.dataset.language === language));
    });
    document.querySelectorAll(".chat-category[data-name-en]").forEach((button) => {
      const label = button.querySelector(".category-label");
      if (label) label.textContent = language === "ha" ? button.dataset.nameHa : button.dataset.nameEn;
    });
    document.querySelectorAll(".suggestion-button").forEach((button) => {
      const label = button.querySelector(".suggestion-text");
      if (label) label.textContent = language === "ha" ? button.dataset.questionHa : button.dataset.questionEn;
    });
    const topicLabel = document.getElementById("activeTopicLabel");
    if (topicLabel) {
      if (selectedCategory) {
        const catBtn = document.querySelector(`.chat-category[data-category="${selectedCategory}"]`);
        if (catBtn) {
          topicLabel.textContent = language === "ha" ? (catBtn.dataset.nameHa || catBtn.textContent.trim()) : (catBtn.dataset.nameEn || catBtn.textContent.trim());
        }
      } else {
        topicLabel.textContent = text("allServices");
      }
    }
  }

  function setBusy(value) {
    busy = value;
    input.disabled = value;
    sendButton.disabled = value || !input.value.trim();
    typing.classList.toggle("d-none", !value);
    if (value) scrollToEnd();
  }

  function appendUserMessage(message, timestamp = new Date()) {
    const row = make("div", "chat-message user-message dynamic-message");
    const column = make("div", "message-column");
    column.append(make("div", "user-bubble", message));
    const time = make("time", "message-time", currentTime(timestamp));
    column.append(time);
    row.append(column);
    pane.append(row);
    scrollToEnd();
  }

  function appendError() {
    appendBotMessage({ answer: text("error"), matched: false, suggestions: [], timestamp: new Date() });
  }

  function suggestionButton(suggestion) {
    const button = make("button", "", suggestion.question);
    button.type = "button";
    button.addEventListener("click", () => sendQuestion(suggestion.question));
    return button;
  }

  function feedbackControls(messageId) {
    const footer = make("div", "answer-footer");
    footer.append(make("span", "", text("helpful")));
    [[true, "hand-thumbs-up", "yes"], [false, "hand-thumbs-down", "no"]].forEach(([helpful, iconName, label]) => {
      const button = make("button", "feedback-btn");
      button.type = "button";
      button.setAttribute("aria-label", text(label));
      button.append(icon(iconName), document.createTextNode(` ${text(label)}`));
      button.addEventListener("click", async () => {
        try {
          const response = await fetch(app.dataset.feedbackUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
            credentials: "same-origin",
            body: JSON.stringify({ message_id: messageId, helpful }),
          });
          if (!response.ok) throw new Error("feedback failed");
          footer.replaceChildren(make("span", "feedback-thanks", text("thanks")));
        } catch (_error) {
          button.disabled = false;
        }
      });
      footer.append(button);
    });
    return footer;
  }

  function appendBotMessage(data, fromHistory = false) {
    const row = make("div", "chat-message bot-message dynamic-message");
    const avatar = make("span", "message-avatar");
    avatar.append(icon("bank2"));
    const column = make("div", "message-column");
    const bubble = make("div", "answer-bubble");

    if (data.category) {
      const meta = make("div", "answer-meta");
      meta.append(make("span", "answer-category", data.category.name));
      if (data.confidence !== undefined) {
        meta.append(make("span", "confidence-label", `${Math.round(data.confidence)}% ${text("verified").toLowerCase()}`));
      }
      bubble.append(meta);
    }
    const answerP = make("p", "answer-text", data.answer || data.message);
    bubble.append(answerP);

    // Bilingual instant toggle: allow toggling answer to English or Hausa
    const answerEn = data.answer_en;
    const answerHa = data.answer_ha;
    if (answerEn && answerHa) {
      let isEnglish = (data.language === "en" || (!data.language && answerP.textContent === answerEn));
      const toggleWrap = make("div", "answer-lang-toggle-wrap");
      const toggleBtn = make("button", "btn-answer-lang-toggle");
      toggleBtn.type = "button";
      toggleBtn.innerHTML = isEnglish
        ? '<i class="bi bi-translate me-1"></i> Duba da Hausa (HA)'
        : '<i class="bi bi-translate me-1"></i> View in English (EN)';
      toggleBtn.addEventListener("click", () => {
        isEnglish = !isEnglish;
        answerP.textContent = isEnglish ? answerEn : answerHa;
        toggleBtn.innerHTML = isEnglish
          ? '<i class="bi bi-translate me-1"></i> Duba da Hausa (HA)'
          : '<i class="bi bi-translate me-1"></i> View in English (EN)';
      });
      toggleWrap.append(toggleBtn);
      bubble.append(toggleWrap);
    }

    if (data.source?.url) {
      const source = make("a", "source-card");
      source.href = data.source.url;
      source.target = "_blank";
      source.rel = "noreferrer";
      source.append(icon("box-arrow-up-right"));
      const sourceText = make("span");
      sourceText.append(make("small", "", data.source.verification_status === "awaiting" ? text("awaiting") : text("source")));
      sourceText.append(make("strong", "", data.source.name || data.source.url));
      source.append(sourceText, icon("arrow-up-right"));
      bubble.append(source);
    } else if (data.source?.verification_status === "awaiting") {
      const warning = make("div", "awaiting-source", text("awaiting"));
      bubble.append(warning);
    }

    if (data.suggestions?.length) {
      const related = make("div", "related-chat");
      related.append(make("span", "", text("related")));
      const list = make("div", "related-chat-list");
      data.suggestions.forEach((item) => list.append(suggestionButton(item)));
      related.append(list);
      bubble.append(related);
    }

    if (!fromHistory && data.message_id) bubble.append(feedbackControls(data.message_id));
    column.append(bubble, make("time", "message-time", currentTime(data.timestamp || data.created_at || new Date())));
    row.append(avatar, column);
    pane.append(row);
    scrollToEnd();
  }

  async function sendQuestion(question) {
    const message = (question || input.value).trim();
    if (!message || busy) return;
    appendUserMessage(message);
    input.value = "";
    setBusy(true);
    try {
      const response = await fetch(app.dataset.messageUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
        credentials: "same-origin",
        body: JSON.stringify({
          message,
          preferred_language: language,
          category: selectedCategory,
        }),
      });
      if (!response.ok) throw new Error(`chat request failed: ${response.status}`);
      const data = await response.json();
      appendBotMessage(data);
      if (data.sensitive_data_redacted) {
        redactionNotice.textContent = text("redacted");
        redactionNotice.classList.remove("d-none");
        window.setTimeout(() => redactionNotice.classList.add("d-none"), 6000);
      }
    } catch (_error) {
      appendError();
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  async function loadHistory() {
    try {
      const response = await fetch(app.dataset.historyUrl, { credentials: "same-origin" });
      if (!response.ok) return;
      const data = await response.json();
      if (!data.messages?.length) return;
      data.messages.forEach((message) => {
        if (message.sender === "user") appendUserMessage(message.message, message.created_at);
        else appendBotMessage({ ...message, answer: message.message, answer_en: message.answer_en, answer_ha: message.answer_ha, matched: Boolean(message.faq_id), suggestions: [] }, true);
      });
    } catch (_error) {
      // The static welcome remains a complete fallback when history cannot load.
    }
  }

  async function loadSuggestions(category = "") {
    const params = new URLSearchParams({ language });
    if (category) params.set("category", category);
    else params.set("featured", "true");
    try {
      const response = await fetch(`${app.dataset.faqUrl}?${params}`, { credentials: "same-origin" });
      if (!response.ok) return;
      const payload = await response.json();
      const faqs = Array.isArray(payload) ? payload : payload.results || [];
      const container = document.getElementById("welcomeSuggestions");
      container.replaceChildren();
      faqs.slice(0, 6).forEach((faq) => {
        const button = make("button", "suggestion-button");
        button.type = "button";
        button.dataset.questionEn = faq.question_en;
        button.dataset.questionHa = faq.question_ha;
        const label = make("span", "suggestion-text", faq.question);
        button.append(label, icon("chevron-right"));
        button.addEventListener("click", () => sendQuestion(faq.question));
        container.append(button);
      });
      if (!faqs.length) container.append(make("span", "no-suggestions", text("noPublished")));
    } catch (_error) {
      // Keep server-rendered suggestions.
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendQuestion();
  });
  input.addEventListener("input", () => { sendButton.disabled = busy || !input.value.trim(); });

  document.querySelectorAll(".suggestion-button").forEach((button) => {
    button.addEventListener("click", () => {
      const question = language === "ha" ? button.dataset.questionHa : button.dataset.questionEn;
      sendQuestion(question);
    });
  });
  document.querySelectorAll(".chat-category").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".chat-category").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      selectedCategory = button.dataset.category || "";
      const topicLabel = document.getElementById("activeTopicLabel");
      if (topicLabel) {
        if (selectedCategory) {
          topicLabel.textContent = language === "ha" ? (button.dataset.nameHa || button.textContent.trim()) : (button.dataset.nameEn || button.textContent.trim());
        } else {
          topicLabel.textContent = text("allServices");
        }
      }
      loadSuggestions(selectedCategory);
    });
  });

  document.querySelectorAll(".composer-chip").forEach((button) => {
    button.addEventListener("click", () => {
      const q = language === "ha" ? button.dataset.questionHa : button.dataset.questionEn;
      if (q) {
        input.value = q;
        sendQuestion(q);
      }
    });
  });
  document.querySelectorAll(".chat-language-control [data-language]").forEach((button) => {
    button.addEventListener("click", () => {
      applyLanguage(button.dataset.language);
      loadSuggestions(selectedCategory);
    });
  });
  clearButton.addEventListener("click", async () => {
    if (!window.confirm(text("clearConfirm"))) return;
    try {
      const response = await fetch(app.dataset.clearUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("clear failed");
      document.querySelectorAll(".dynamic-message").forEach((message) => message.remove());
      selectedCategory = "";
      document.querySelectorAll(".chat-category").forEach((button, index) => button.classList.toggle("active", index === 0));
      pane.scrollTop = 0;
    } catch (_error) {
      appendError();
    }
  });

  document.querySelectorAll(".language-choice").forEach((button) => {
    button.addEventListener("click", () => {
      applyLanguage(button.dataset.language);
      window.bootstrap.Modal.getInstance(document.getElementById("languageChoiceModal"))?.hide();
      input.focus();
      loadSuggestions();
    });
  });

  if (!language || !["en", "ha"].includes(language)) {
    language = "en";
    applyLanguage(language, false);
    window.addEventListener("DOMContentLoaded", () => {
      window.bootstrap.Modal.getOrCreateInstance(document.getElementById("languageChoiceModal")).show();
    });
  } else {
    applyLanguage(language, false);
  }

  // Handle URL query parameters (deep-linking from Home or FAQ search)
  const urlParams = new URLSearchParams(window.location.search);
  const paramLang = urlParams.get("language") || urlParams.get("lang");
  if (paramLang && ["en", "ha"].includes(paramLang)) {
    applyLanguage(paramLang, true);
  }
  const paramCategory = urlParams.get("category");
  if (paramCategory) {
    const targetCat = document.querySelector(`.chat-category[data-category="${paramCategory}"]`);
    if (targetCat) {
      document.querySelectorAll(".chat-category").forEach((item) => item.classList.remove("active"));
      targetCat.classList.add("active");
      selectedCategory = paramCategory;
      const topicLabel = document.getElementById("activeTopicLabel");
      if (topicLabel) {
        topicLabel.textContent = language === "ha" ? (targetCat.dataset.nameHa || targetCat.textContent.trim()) : (targetCat.dataset.nameEn || targetCat.textContent.trim());
      }
    }
  }
  const paramQuestion = urlParams.get("q");
  if (paramQuestion) {
    window.setTimeout(() => {
      input.value = paramQuestion;
      sendQuestion(paramQuestion);
      const cleanUrl = window.location.pathname + (selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : "");
      window.history.replaceState({}, "", cleanUrl);
    }, 450);
  }

  sendButton.disabled = true;
  loadHistory();
})();
