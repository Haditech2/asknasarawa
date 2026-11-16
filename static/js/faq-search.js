(() => {
  "use strict";
  const form = document.getElementById("faqSearchForm");
  if (!form || !window.fetch) return;

  const results = document.getElementById("faqResults");
  const status = document.getElementById("faqSearchStatus");
  const summary = document.getElementById("searchSummary");
  const queryInput = document.getElementById("faqQuery");
  const categoryInput = document.getElementById("faqCategory");
  const languageInput = document.getElementById("faqLanguage");

  function make(tag, className, value) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (value !== undefined) element.textContent = value;
    return element;
  }

  function badge(label, className, iconName) {
    const span = make("span", className);
    const icon = make("i", `bi bi-${iconName}`);
    span.append(icon, document.createTextNode(` ${label}`));
    return span;
  }

  function renderEmpty(language) {
    const empty = make("div", "empty-state search-empty");
    empty.append(make("i", "bi bi-search"));
    empty.append(make("h2", "", language === "ha" ? "Ba a sami amsa ba" : "No matching FAQ found"));
    empty.append(make("p", "", language === "ha" ? "Ka gwada wata kalma ko ka yi tambaya a chatbot." : "Try another keyword or ask the chatbot so the question can be reviewed."));
    const link = make("a", "btn btn-outline-gov", language === "ha" ? "Yi tambaya" : "Ask the assistant");
    link.href = "/chat/";
    empty.append(link);
    results.append(empty);
  }

  function renderFaq(item, language) {
    const faq = item.faq;
    const card = make("article", "faq-result-card");
    const main = make("div", "faq-result-main");
    const badges = make("div", "d-flex align-items-center gap-2 mb-2");
    badges.append(badge(faq.category.name, "category-chip", faq.category.icon.replace(/^bi-/, "")));
    const verified = faq.verification_status === "verified";
    badges.append(badge(
      verified ? (language === "ha" ? "An tabbatar" : "Verified") : (language === "ha" ? "Ana jiran tabbaci" : "Awaiting confirmation"),
      verified ? "verified-chip" : "awaiting-chip",
      verified ? "patch-check-fill" : "clock",
    ));
    const heading = make("h2");
    const link = make("a", "", faq.question);
    link.href = `/faqs/${faq.id}/?language=${language}`;
    heading.append(link);
    const answer = faq.answer.length > 330 ? `${faq.answer.slice(0, 327)}…` : faq.answer;
    main.append(badges, heading, make("p", "", answer));
    const arrow = make("a", "faq-result-arrow");
    arrow.href = link.href;
    arrow.setAttribute("aria-label", language === "ha" ? "Buɗe amsa" : "Open answer");
    arrow.append(make("i", "bi bi-arrow-right"));
    card.append(main, arrow);
    results.append(card);
  }

  async function search(event) {
    if (event) event.preventDefault();
    const query = queryInput.value.trim();
    const category = categoryInput.value;
    const language = languageInput.value;
    if (!query) {
      form.submit();
      return;
    }
    status.textContent = language === "ha" ? "Ana bincike…" : "Searching…";
    form.setAttribute("aria-busy", "true");
    const params = new URLSearchParams({ q: query, category, language });
    try {
      const response = await fetch(`${form.dataset.searchUrl}?${params}`, { credentials: "same-origin" });
      if (!response.ok) throw new Error("search failed");
      const data = await response.json();
      results.replaceChildren();
      data.results.forEach((item) => renderFaq(item, language));
      if (!data.results.length) renderEmpty(language);
      summary.textContent = language === "ha" ? `${data.count} sakamako don “${query}”` : `${data.count} result${data.count === 1 ? "" : "s"} for “${query}”`;
      status.textContent = summary.textContent;
      window.history.replaceState({}, "", `${window.location.pathname}?${params}`);
    } catch (_error) {
      status.textContent = language === "ha" ? "Binciken bai yiwu ba. Ka sake gwadawa." : "Search could not be completed. Please try again.";
    } finally {
      form.removeAttribute("aria-busy");
    }
  }

  form.addEventListener("submit", search);
  categoryInput.addEventListener("change", () => {
    if (queryInput.value.trim()) search();
    else form.submit();
  });

  let debounceTimer;
  queryInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = queryInput.value.trim();
      if (q.length >= 2) {
        search();
      } else if (q.length === 0) {
        form.submit();
      }
    }, 350);
  });

  // Keyboard shortcut: Press "/" to focus search input
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== queryInput && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
      e.preventDefault();
      queryInput.focus();
    }
  });
})();
