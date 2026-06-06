// dashboard.js
let rawData = [];
let filters = { sucursal: 'all', categoria: 'all', cliente: 'all' };

// 1. Cargar datos
async function init() {
    try {
        const res = await fetch('./data/ventas.json');
        rawData = await res.json();
        populateFilters();
        updateDashboard();
        document.getElementById('lastUpdate').textContent = new Date().toLocaleDateString('es-MX');
    } catch (err) {
        console.error('Error cargando datos:', err);
        document.body.innerHTML = '<h2 style="text-align:center;margin-top:20%;color:#ef4444">Error: No se encontró data/ventas.json</h2>';
    }
}

// 2. Poblar dropdowns
function populateFilters() {
    const sucursales = [...new Set(rawData.map(d => d.sucursal))].sort();
    const categorias = [...new Set(rawData.map(d => d.categoria))].sort();
    const clientes = [...new Set(rawData.map(d => d.tipo_cliente))].sort();

    addOptions('sucursalFilter', sucursales);
    addOptions('categoriaFilter', categorias);
    addOptions('clienteFilter', clientes);

    // Listeners
    ['sucursalFilter', 'categoriaFilter', 'clienteFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', e => {
            filters[id.replace('Filter', '')] = e.target.value;
            updateDashboard();
        });
    });
}

function addOptions(id, arr) {
    const sel = document.getElementById(id);
    arr.forEach(val => {
        const opt = document.createElement('option');
        opt.value = val; opt.textContent = val;
        sel.appendChild(opt);
    });
}

// 3. Filtrar y actualizar
function updateDashboard() {
    let data = rawData.filter(d => 
        (filters.sucursal === 'all' || d.sucursal === filters.sucursal) &&
        (filters.categoria === 'all' || d.categoria === filters.categoria) &&
        (filters.cliente === 'all' || d.tipo_cliente === filters.cliente)
    );

    renderKPIs(data);
    renderCharts(data);
}

function renderKPIs(data) {
    const totalVentas = data.length;
    const ingresos = data.reduce((s, d) => s + d.total_venta, 0);
    const margen = data.reduce((s, d) => s + d.margen, 0);
    const ticket = totalVentas ? ingresos / totalVentas : 0;

    document.getElementById('kpi-ventas').textContent = totalVentas.toLocaleString();
    document.getElementById('kpi-ingresos').textContent = `$${ingresos.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    document.getElementById('kpi-margen').textContent = `$${margen.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    document.getElementById('kpi-ticket').textContent = `$${ticket.toFixed(2)}`;
}

function renderCharts(data) {
    // Agrupaciones
    const byCat = groupBy(data, 'categoria', 'total_venta');
    const bySuc = groupBy(data, 'sucursal', 'total_venta');
    const byCli = groupBy(data, 'tipo_cliente', 'total_venta');
    const byZona = groupBy(data, 'zona', 'margen');
    
    // Tendencia mensual
    const monthly = {};
    data.forEach(d => {
        const mes = d.fecha.substring(0, 7); // YYYY-MM
        monthly[mes] = (monthly[mes] || 0) + d.total_venta;
    });
    const trendLabels = Object.keys(monthly).sort();
    const trendVals = trendLabels.map(m => monthly[m]);

    // Gráfica Categoría
    Plotly.newPlot('chart-cat', [{
        x: byCat.labels, y: byCat.values, type: 'bar', marker: { color: '#3b82f6' }
    }], { margin: {t: 20}, yaxis: {title: 'Ingresos ($)'} });

    // Gráfica Sucursal
    Plotly.newPlot('chart-suc', [{
        x: bySuc.labels, y: bySuc.values, type: 'bar', marker: { color: '#10b981' }
    }], { margin: {t: 20}, xaxis: {tickangle: -45}, yaxis: {title: 'Ingresos ($)'} });

    // Gráfica Tendencia
    Plotly.newPlot('chart-trend', [{
        x: trendLabels, y: trendVals, mode: 'lines+markers', line: {color: '#8b5cf6', width: 3}, marker: {size: 6}
    }], { margin: {t: 20}, xaxis: {title: 'Mes'}, yaxis: {title: 'Ingresos ($)'} });

    // Gráfica Cliente
    Plotly.newPlot('chart-cli', [{
        labels: byCli.labels, values: byCli.values, type: 'pie', hole: 0.4, marker: {colors: ['#f59e0b', '#ef4444', '#06b6d4', '#84cc16']}
    }], { margin: {t: 20} });

    // Gráfica Zona (Margen)
    Plotly.newPlot('chart-zona', [{
        x: byZona.labels, y: byZona.values, type: 'bar', marker: {color: '#ec4899'}
    }], { margin: {t: 20}, yaxis: {title: 'Margen Neto ($)'} });
}

function groupBy(arr, key, sumKey) {
    const map = {};
    arr.forEach(d => { map[d[key]] = (map[d[key]] || 0) + d[sumKey]; });
    return { labels: Object.keys(map), values: Object.values(map) };
}

// Iniciar
document.addEventListener('DOMContentLoaded', init);