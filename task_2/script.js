const PALETTE = ["#0B3D91", "#1D7A8C", "#E07A3D", "#C0392B", "#5B4B8A", "#2E8B57"];

const COLUMNS = [
  ["district", "District"],
  ["province", "Province"],
  ["deaths_recovered", "Recovered deaths"],
  ["share_of_national_pct", "Share %"],
  ["rdna_people_affected", "RDNA people"],
  ["rdna_houses_damaged", "RDNA houses"],
  ["notes", "Notes"],
];

let rows = [];
let deathsChart;
let housesChart;
let map;
let markers = [];

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    const row = {};
    headers.forEach((header, i) => {
      row[header] = values[i] ?? "";
    });
    row.deaths_recovered = Number(row.deaths_recovered) || 0;
    row.share_of_national_pct = Number(row.share_of_national_pct) || 0;
    row.rdna_people_affected = row.rdna_people_affected === "" ? null : Number(row.rdna_people_affected);
    row.rdna_houses_damaged = row.rdna_houses_damaged === "" ? null : Number(row.rdna_houses_damaged);
    row.lat = Number(row.lat);
    row.lon = Number(row.lon);
    return row;
  });
}

function splitCsvLine(line) {
  const out = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      out.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  out.push(current);
  return out;
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("en-US");
}

function currentFilters() {
  return {
    province: document.getElementById("provinceFilter").value,
    minDeaths: Number(document.getElementById("minDeaths").value),
    search: document.getElementById("search").value.trim().toLowerCase(),
  };
}

function filteredRows() {
  const { province, minDeaths, search } = currentFilters();
  return rows.filter((row) => {
    if (province !== "All" && row.province !== province) return false;
    if (row.deaths_recovered < minDeaths) return false;
    if (search && !row.district.toLowerCase().includes(search)) return false;
    return true;
  });
}

function renderMetrics(data) {
  const deaths = data.reduce((sum, row) => sum + row.deaths_recovered, 0);
  const people = data.reduce((sum, row) => sum + (row.rdna_people_affected || 0), 0);
  const houses = data.reduce((sum, row) => sum + (row.rdna_houses_damaged || 0), 0);
  const items = [
    ["Recovered deaths", deaths],
    ["RDNA people affected", people],
    ["RDNA houses damaged", houses],
    ["Districts shown", data.length],
  ];
  document.getElementById("metrics").innerHTML = items
    .map(
      ([label, value]) =>
        `<article class="metric"><span>${label}</span><strong>${formatNumber(value)}</strong></article>`
    )
    .join("");
}

function chartConfig(labels, values, color) {
  return {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: color,
          borderWidth: 0,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { grid: { color: "#E6EEF4" }, ticks: { color: "#1B2430" } },
        y: { grid: { display: false }, ticks: { color: "#1B2430" } },
      },
    },
  };
}

function renderCharts(data) {
  const sortedDeaths = [...data].sort((a, b) => a.deaths_recovered - b.deaths_recovered);
  const rdna = [...data]
    .filter((row) => row.rdna_houses_damaged !== null)
    .sort((a, b) => a.rdna_houses_damaged - b.rdna_houses_damaged);

  const deathsPayload = chartConfig(
    sortedDeaths.map((row) => row.district),
    sortedDeaths.map((row) => row.deaths_recovered),
    PALETTE[0]
  );
  const housesPayload = chartConfig(
    rdna.map((row) => row.district),
    rdna.map((row) => row.rdna_houses_damaged),
    PALETTE[1]
  );

  if (deathsChart) deathsChart.destroy();
  if (housesChart) housesChart.destroy();
  deathsChart = new Chart(document.getElementById("deathsChart"), deathsPayload);
  housesChart = new Chart(document.getElementById("housesChart"), housesPayload);
}

function renderTable(data) {
  const thead = document.querySelector("#dataTable thead");
  const tbody = document.querySelector("#dataTable tbody");
  thead.innerHTML = `<tr>${COLUMNS.map(([, label]) => `<th>${label}</th>`).join("")}</tr>`;
  tbody.innerHTML = data
    .map((row) => {
      const cells = COLUMNS.map(([key]) => {
        const value = row[key];
        if (typeof value === "number") return `<td>${formatNumber(value)}</td>`;
        return `<td>${value || "—"}</td>`;
      }).join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");
}

function renderMap(data) {
  if (!map) {
    map = L.map("map").setView([27.9, 84.7], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);
  }
  markers.forEach((marker) => marker.remove());
  markers = data
    .filter((row) => Number.isFinite(row.lat) && Number.isFinite(row.lon))
    .map((row) => {
      const radius = 6 + Math.sqrt(row.deaths_recovered) * 1.2;
      const marker = L.circleMarker([row.lat, row.lon], {
        radius,
        color: PALETTE[0],
        fillColor: PALETTE[2],
        fillOpacity: 0.85,
        weight: 1,
      }).addTo(map);
      marker.bindPopup(
        `<strong>${row.district}</strong><br>${formatNumber(row.deaths_recovered)} recovered deaths`
      );
      return marker;
    });
}

function render() {
  const data = filteredRows();
  renderMetrics(data);
  renderCharts(data);
  renderTable(data);
  renderMap(data);
}

function populateFilters() {
  const select = document.getElementById("provinceFilter");
  const provinces = [...new Set(rows.map((row) => row.province))].sort();
  provinces.forEach((province) => {
    const option = document.createElement("option");
    option.value = province;
    option.textContent = province;
    select.appendChild(option);
  });
  const maxDeaths = Math.max(...rows.map((row) => row.deaths_recovered));
  const slider = document.getElementById("minDeaths");
  slider.max = String(maxDeaths);
  slider.value = "0";
}

function bindEvents() {
  ["provinceFilter", "minDeaths", "search"].forEach((id) => {
    document.getElementById(id).addEventListener("input", () => {
      document.getElementById("minDeathsLabel").textContent =
        document.getElementById("minDeaths").value;
      render();
    });
  });
}

async function init() {
  try {
    const response = await fetch("flood_data_filtered.csv");
    if (!response.ok) {
      throw new Error("Could not load flood_data_filtered.csv");
    }
    rows = parseCsv(await response.text());
    populateFilters();
    bindEvents();
    render();
  } catch (error) {
    document.body.insertAdjacentHTML(
      "afterbegin",
      `<p class="error">${error.message}. Open this site from an HTTP URL (S3 website or local server), not as a local file.</p>`
    );
  }
}

init();
