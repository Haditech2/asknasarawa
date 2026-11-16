(() => {
  "use strict";
  const root = document.getElementById("analyticsDashboard");
  if (!root || typeof window.Chart === "undefined") return;

  const period = document.getElementById("analyticsPeriod");
  let dailyChart;
  let languageChart;

  function languageData(data) {
    const counts = { en: 0, ha: 0 };
    data.language_usage.forEach((row) => { counts[row.language] = row.count; });
    return counts;
  }

  function charts(data) {
    const dailyContext = document.getElementById("dailyChart");
    const languageContext = document.getElementById("languageChart");
    dailyChart?.destroy();
    languageChart?.destroy();
    dailyChart = new window.Chart(dailyContext, {
      type: "line",
      data: {
        labels: data.daily_usage.map((row) => new Date(`${row.date}T12:00:00`).toLocaleDateString(undefined, { day: "numeric", month: "short" })),
        datasets: [{
          label: "Questions",
          data: data.daily_usage.map((row) => row.count),
          borderColor: "#0b5745",
          backgroundColor: "rgba(11, 87, 69, 0.12)",
          fill: true,
          borderWidth: 2.5,
          pointRadius: data.period_days > 90 ? 0 : 3,
          pointBackgroundColor: "#0b5745",
          pointHoverRadius: 5,
          tension: 0.35,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#04251d",
            borderColor: "rgba(199, 148, 46, 0.5)",
            borderWidth: 1,
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: "700" },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
            padding: 10,
            cornerRadius: 8,
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxTicksLimit: 10, color: "#526f65", font: { size: 11, family: "'Plus Jakarta Sans', sans-serif" } },
          },
          y: {
            beginAtZero: true,
            ticks: { precision: 0, color: "#526f65", font: { size: 11, family: "'Plus Jakarta Sans', sans-serif" } },
            grid: { color: "#e6eee9" },
          },
        },
      },
    });
    const languages = languageData(data);
    languageChart = new window.Chart(languageContext, {
      type: "doughnut",
      data: {
        labels: ["English", "Hausa"],
        datasets: [{
          data: [languages.en, languages.ha],
          backgroundColor: ["#0b5745", "#c7942e"],
          borderWidth: 2,
          borderColor: "#ffffff",
          hoverOffset: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#04251d",
            borderColor: "rgba(199, 148, 46, 0.5)",
            borderWidth: 1,
            titleFont: { family: "'Plus Jakarta Sans', sans-serif" },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
            padding: 10,
            cornerRadius: 8,
          },
        },
      },
    });
    const legend = document.getElementById("languageLegend");
    legend.replaceChildren();
    [["English", languages.en, "#0b5745"], ["Hausa", languages.ha, "#c7942e"]].forEach(([label, count, color]) => {
      const span = document.createElement("span");
      const dot = document.createElement("i");
      dot.style.backgroundColor = color;
      span.append(dot, document.createTextNode(`${label} · ${count}`));
      legend.append(span);
    });
  }

  function updateTable(data) {
    const body = document.getElementById("topFaqTable");
    body.replaceChildren();
    if (!data.top_faqs.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 2;
      cell.className = "empty-cell";
      cell.textContent = "No matched questions in this period.";
      row.append(cell);
      body.append(row);
      return;
    }
    data.top_faqs.forEach((item) => {
      const row = document.createElement("tr");
      const question = document.createElement("td");
      question.textContent = item.matched_faq__question_en;
      const count = document.createElement("td");
      count.className = "text-end";
      const badge = document.createElement("span");
      badge.textContent = item.count;
      count.append(badge);
      row.append(question, count);
      body.append(row);
    });
  }

  function updateUnanswered(data) {
    const box = document.getElementById("unansweredSummary");
    box.replaceChildren();
    if (!data.unanswered_by_status.length) {
      const empty = document.createElement("div");
      empty.className = "empty-cell";
      empty.textContent = "No unanswered questions in this period.";
      box.append(empty);
      return;
    }
    data.unanswered_by_status.forEach((item) => {
      const block = document.createElement("div");
      const label = document.createElement("span");
      label.textContent = item.status.charAt(0).toUpperCase() + item.status.slice(1);
      const count = document.createElement("strong");
      count.textContent = item.count;
      block.append(label, count);
      box.append(block);
    });
  }

  function render(data) {
    document.getElementById("metricConversations").textContent = data.totals.conversations;
    document.getElementById("metricQuestions").textContent = data.totals.questions;
    document.getElementById("metricSearches").textContent = data.totals.searches;
    document.getElementById("metricUnanswered").textContent = data.totals.unanswered;
    document.getElementById("metricPublished").textContent = data.totals.published_faqs;
    document.getElementById("chartPeriodLabel").textContent = `${data.period_days}-day view`;
    charts(data);
    updateTable(data);
    updateUnanswered(data);
  }

  period.addEventListener("change", async () => {
    period.disabled = true;
    try {
      const response = await fetch(`${root.dataset.apiUrl}?days=${period.value}`, { credentials: "same-origin" });
      if (!response.ok) throw new Error("analytics failed");
      render(await response.json());
    } finally {
      period.disabled = false;
    }
  });

  fetch(`${root.dataset.apiUrl}?days=30`, { credentials: "same-origin" })
    .then((response) => {
      if (!response.ok) throw new Error("analytics failed");
      return response.json();
    })
    .then(render)
    .catch(() => {
      document.getElementById("chartPeriodLabel").textContent = "Unable to load chart data";
    });
})();
