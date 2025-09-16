(() => {
  const state = {
    nodes: [],
    links: [],
    users: [],
    nodeMap: new Map(),
    worldview: null,
  };

  let currentView = 'blob';
  let currentInventoryUser = null;
  let currentComparisonLeft = null;
  let currentComparisonRight = null;
  let currentDimensionX = 0;
  let currentDimensionY = 1;

  const statusIndicator = document.getElementById('status-indicator');
  const tooltip = document.getElementById('tooltip');

  const linkTargetSelect = document.getElementById('link-target-select');
  const inventoryUserSelect = document.getElementById('inventory-user');
  const comparisonLeftSelect = document.getElementById('comparison-left-user');
  const comparisonRightSelect = document.getElementById('comparison-right-user');
  const opinionUserSelect = document.getElementById('opinion-user-select');
  const opinionNodeSelect = document.getElementById('opinion-node-select');
  const dimensionXSelect = document.getElementById('dimension-x');
  const dimensionYSelect = document.getElementById('dimension-y');

  const svgElements = {
    blob: document.getElementById('blob-svg'),
    inventory: document.getElementById('inventory-svg'),
    comparisonLeft: document.getElementById('comparison-left'),
    comparisonRight: document.getElementById('comparison-right'),
    worldview: document.getElementById('worldview-svg'),
  };

  function safe(text) {
    return (text || '').replace(/[&<>"]/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
    })[char]);
  }

  function updateStatus(text, ready = false) {
    statusIndicator.textContent = text;
    statusIndicator.classList.toggle('ready', ready);
  }

  function buildStateMaps() {
    state.nodeMap = new Map(state.nodes.map((node) => [node.id, node]));
  }

  function populateSelect(select, items, { valueKey, labelKey, includeEmpty }) {
    if (!select) return;
    const previous = select.value;
    select.innerHTML = '';
    if (includeEmpty) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '— none —';
      select.appendChild(opt);
    }
    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = item[valueKey];
      option.textContent = item[labelKey];
      select.appendChild(option);
    });
    if (previous && items.some((item) => item[valueKey] === previous)) {
      select.value = previous;
    }
  }

  function formatOpinions(opinions) {
    if (!opinions || !opinions.length) return '<em>No opinions yet</em>';
    return opinions
      .map((opinion) => {
        const stance = opinion.stance === 'support' ? 'supports' : opinion.stance === 'contradict' ? 'contradicts' : 'neutral';
        return `<div class="opinion-line"><strong>${safe(opinion.user_id)}</strong> ${stance}<br />` +
          `<span>Agreement: ${(opinion.agreement * 100).toFixed(0)}% · Confidence: ${(opinion.confidence * 100).toFixed(0)}%</span></div>`;
      })
      .join('');
  }

  function showTooltip(node, event) {
    tooltip.hidden = false;
    tooltip.innerHTML = `
      <strong>${safe(node.title)}</strong>
      <div class="tooltip-summary">${safe(node.summary || 'No summary available')}</div>
      <div class="tooltip-meta">Type: ${safe(node.type)}${node.source ? ` · Source: ${safe(node.source)}` : ''}</div>
      <div class="tooltip-tags">${(node.tags || []).map((tag) => `#${safe(tag)}`).join(' ')}</div>
      <div class="tooltip-opinions">${formatOpinions(node.opinions)}</div>
    `;
    moveTooltip(event);
  }

  function moveTooltip(event) {
    const offset = 18;
    tooltip.style.left = `${event.clientX + offset}px`;
    tooltip.style.top = `${event.clientY + offset}px`;
  }

  function hideTooltip() {
    tooltip.hidden = true;
  }

  function nodeRadius(node) {
    const base = 18 + (node.importance || 0.5) * 20;
    const extra = node.type === 'news' ? 6 : node.type === 'analysis' ? 10 : 0;
    return base + extra;
  }

  function createMarkers(svg, prefix) {
    const defs = svg.append('defs');
    const relationships = ['supports', 'contradicts', 'relates'];
    const colors = {
      supports: '#1a936f',
      contradicts: '#ef476f',
      relates: '#577590',
    };
    relationships.forEach((relationship) => {
      defs
        .append('marker')
        .attr('id', `${prefix}-${relationship}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', colors[relationship]);
    });
  }

  function renderForceGraph(svgElement, nodes, links, options = {}) {
    const svg = d3.select(svgElement);
    svg.selectAll('*').remove();
    const { width, height } = svgElement.viewBox.baseVal;
    const markerPrefix = `arrow-${Math.random().toString(36).slice(2, 8)}`;
    createMarkers(svg, markerPrefix);

    const nodeData = nodes.map((node) => ({ ...node }));
    const linkData = links.map((link) => ({ ...link }));

    const linkForce = d3
      .forceLink(linkData)
      .id((d) => d.id)
      .distance((d) => 180 - Math.min(120, (d.weight || 0.4) * 140))
      .strength(0.4);

    const simulation = d3
      .forceSimulation(nodeData)
      .force('link', linkForce)
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d) => nodeRadius(d) + 6));

    const linkGroup = svg.append('g').attr('class', 'links');
    const nodeGroup = svg.append('g').attr('class', 'nodes');

    const linkElements = linkGroup
      .selectAll('line')
      .data(linkData)
      .enter()
      .append('line')
      .attr('class', (d) => `link ${d.relationship}`)
      .attr('marker-end', (d) => `url(#${markerPrefix}-${d.relationship || 'relates'})`);

    const nodeElements = nodeGroup
      .selectAll('g')
      .data(nodeData)
      .enter()
      .append('g')
      .attr('class', (d) => `node ${d.importance > 0.8 ? 'important' : ''}`)
      .on('mouseover', (event, d) => showTooltip(d, event))
      .on('mousemove', (event) => moveTooltip(event))
      .on('mouseout', hideTooltip);

    nodeElements
      .append('circle')
      .attr('r', (d) => nodeRadius(d));

    nodeElements
      .append('text')
      .attr('dy', 4)
      .text((d) => d.title.slice(0, 36));

    simulation.on('tick', () => {
      linkElements
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      nodeElements.attr('transform', (d) => `translate(${d.x}, ${d.y})`);
    });

    return simulation;
  }

  function getUserColor(userId) {
    const user = state.users.find((candidate) => candidate.id === userId);
    return user?.color || '#222';
  }

  function buildUserGraph(userId) {
    const nodes = state.nodes.filter((node) => {
      if (node.creator_user_id === userId) return true;
      return (node.opinions || []).some((opinion) => opinion.user_id === userId);
    });
    const nodeIds = new Set(nodes.map((node) => node.id));
    const links = state.links.filter((link) => nodeIds.has(link.source) && nodeIds.has(link.target));
    return { nodes, links };
  }

  function renderBlobView() {
    renderForceGraph(svgElements.blob, state.nodes, state.links);
  }

  function renderInventoryView() {
    if (!state.users.length) {
      d3.select(svgElements.inventory).selectAll('*').remove();
      return;
    }
    if (!currentInventoryUser || !state.users.some((user) => user.id === currentInventoryUser)) {
      currentInventoryUser = state.users[0].id;
      inventoryUserSelect.value = currentInventoryUser;
    }
    const { nodes, links } = buildUserGraph(currentInventoryUser);
    renderForceGraph(svgElements.inventory, nodes, links);
  }

  function renderComparisonView() {
    if (state.users.length === 0) {
      d3.select(svgElements.comparisonLeft).selectAll('*').remove();
      d3.select(svgElements.comparisonRight).selectAll('*').remove();
      return;
    }
    if (!currentComparisonLeft || !state.users.some((user) => user.id === currentComparisonLeft)) {
      currentComparisonLeft = state.users[0]?.id;
      comparisonLeftSelect.value = currentComparisonLeft;
    }
    if (!currentComparisonRight || !state.users.some((user) => user.id === currentComparisonRight)) {
      currentComparisonRight = state.users[1]?.id || state.users[0]?.id;
      comparisonRightSelect.value = currentComparisonRight;
    }
    const leftGraph = buildUserGraph(currentComparisonLeft);
    const rightGraph = buildUserGraph(currentComparisonRight);
    renderForceGraph(svgElements.comparisonLeft, leftGraph.nodes, leftGraph.links);
    renderForceGraph(svgElements.comparisonRight, rightGraph.nodes, rightGraph.links);
  }

  function renderWorldviewLegend(projections) {
    const legend = document.getElementById('worldview-legend');
    legend.innerHTML = '';
    projections.forEach((projection) => {
      const item = document.createElement('div');
      item.className = 'legend-item';
      const swatch = document.createElement('span');
      swatch.className = 'legend-swatch';
      swatch.style.background = getUserColor(projection.user_id);
      item.appendChild(swatch);
      const label = document.createElement('span');
      label.innerHTML = `<strong>${safe(projection.name)}</strong> · agreement ${(projection.features.agreement * 100).toFixed(0)}% · confidence ${(projection.features.confidence * 100).toFixed(0)}%`;
      item.appendChild(label);
      legend.appendChild(item);
    });
  }

  function renderWorldviewView() {
    const worldview = state.worldview;
    if (!worldview || !worldview.axes.length) {
      d3.select(svgElements.worldview).selectAll('*').remove();
      document.getElementById('worldview-legend').textContent = 'Add more opinions to unlock worldview geometry.';
      return;
    }
    const axesCount = worldview.axes.length;
    if (currentDimensionX >= axesCount) currentDimensionX = 0;
    if (currentDimensionY >= axesCount || currentDimensionY === currentDimensionX) {
      currentDimensionY = axesCount > 1 ? 1 : 0;
    }
    dimensionXSelect.value = String(currentDimensionX);
    dimensionYSelect.value = String(currentDimensionY);

    const svg = d3.select(svgElements.worldview);
    svg.selectAll('*').remove();
    const { width, height } = svgElements.worldview.viewBox.baseVal;

    const projections = worldview.projections.filter((projection) => projection.coordinates.length);
    const xExtent = d3.extent(projections, (p) => p.coordinates[currentDimensionX]) || [-1, 1];
    const yExtent = d3.extent(projections, (p) => p.coordinates[currentDimensionY]) || [-1, 1];

    const padding = 60;
    const xScale = d3.scaleLinear().domain([xExtent[0] - 0.2, xExtent[1] + 0.2]).range([padding, width - padding]);
    const yScale = d3.scaleLinear().domain([yExtent[0] - 0.2, yExtent[1] + 0.2]).range([height - padding, padding]);

    svg
      .append('line')
      .attr('x1', padding / 2)
      .attr('x2', width - padding / 2)
      .attr('y1', yScale(0))
      .attr('y2', yScale(0))
      .attr('stroke', '#bbb')
      .attr('stroke-dasharray', '6 4');

    svg
      .append('line')
      .attr('y1', padding / 2)
      .attr('y2', height - padding / 2)
      .attr('x1', xScale(0))
      .attr('x2', xScale(0))
      .attr('stroke', '#bbb')
      .attr('stroke-dasharray', '6 4');

    const axisLabelGroup = svg.append('g').attr('class', 'axis-labels');
    axisLabelGroup
      .append('text')
      .attr('x', width - padding)
      .attr('y', yScale(0) - 10)
      .attr('text-anchor', 'end')
      .attr('fill', '#333')
      .text(
        `${worldview.axes[currentDimensionX]} (${((worldview.explained_variance[currentDimensionX] || 0) * 100).toFixed(0)}%)`
      );

    axisLabelGroup
      .append('text')
      .attr('x', xScale(0) + 10)
      .attr('y', padding)
      .attr('text-anchor', 'start')
      .attr('fill', '#333')
      .text(
        `${worldview.axes[currentDimensionY]} (${((worldview.explained_variance[currentDimensionY] || 0) * 100).toFixed(0)}%)`
      );

    const group = svg.append('g').attr('class', 'worldview-points');
    projections.forEach((projection) => {
      const cx = xScale(projection.coordinates[currentDimensionX]);
      const cy = yScale(projection.coordinates[currentDimensionY]);
      const color = getUserColor(projection.user_id);
      const rx = 26 + projection.features.confidence * 80;
      const ry = 26 + projection.features.agreement * 80;
      const rotation = (projection.features.contradiction_ratio - projection.features.support_ratio) * 90;

      const shape = group
        .append('g')
        .attr('transform', `translate(${cx}, ${cy}) rotate(${rotation})`);

      shape
        .append('ellipse')
        .attr('rx', rx)
        .attr('ry', ry)
        .attr('fill', color)
        .attr('fill-opacity', 0.18)
        .attr('stroke', color)
        .attr('stroke-width', 2.4);

      shape
        .append('text')
        .attr('transform', `rotate(${-rotation})`)
        .attr('dy', 4)
        .attr('text-anchor', 'middle')
        .attr('fill', '#222')
        .text(projection.name);
    });

    renderWorldviewLegend(projections);
  }

  function renderCurrentView() {
    switch (currentView) {
      case 'blob':
        renderBlobView();
        break;
      case 'inventory':
        renderInventoryView();
        break;
      case 'comparison':
        renderComparisonView();
        break;
      case 'worldview':
        renderWorldviewView();
        break;
      default:
        renderBlobView();
    }
  }

  function setView(view) {
    currentView = view;
    document.querySelectorAll('.view').forEach((section) => section.classList.remove('visible'));
    const currentSection = document.getElementById(`view-${view}`);
    if (currentSection) {
      currentSection.classList.add('visible');
    }
    renderCurrentView();
  }

  function updateSelectors() {
    populateSelect(
      linkTargetSelect,
      state.nodes.map((node) => ({ id: node.id, label: node.title })),
      { valueKey: 'id', labelKey: 'label', includeEmpty: true }
    );
    populateSelect(
      inventoryUserSelect,
      state.users.map((user) => ({ id: user.id, label: user.name })),
      { valueKey: 'id', labelKey: 'label' }
    );
    populateSelect(
      comparisonLeftSelect,
      state.users.map((user) => ({ id: user.id, label: user.name })),
      { valueKey: 'id', labelKey: 'label' }
    );
    populateSelect(
      comparisonRightSelect,
      state.users.map((user) => ({ id: user.id, label: user.name })),
      { valueKey: 'id', labelKey: 'label' }
    );
    populateSelect(
      opinionUserSelect,
      state.users.map((user) => ({ id: user.name, label: user.name })),
      { valueKey: 'id', labelKey: 'label' }
    );
    populateSelect(
      opinionNodeSelect,
      state.nodes.map((node) => ({ id: node.id, label: node.title })),
      { valueKey: 'id', labelKey: 'label' }
    );

    if (state.worldview?.axes?.length) {
      const options = state.worldview.axes.map((axis, index) => ({ id: String(index), label: axis }));
      populateSelect(dimensionXSelect, options, { valueKey: 'id', labelKey: 'label' });
      populateSelect(dimensionYSelect, options, { valueKey: 'id', labelKey: 'label' });
      dimensionXSelect.value = String(Math.min(currentDimensionX, options.length - 1));
      dimensionYSelect.value = String(Math.min(currentDimensionY, options.length - 1));
    }

    if (state.users.length) {
      if (!currentInventoryUser || !state.users.some((user) => user.id === currentInventoryUser)) {
        currentInventoryUser = state.users[0].id;
      }
      inventoryUserSelect.value = currentInventoryUser;

      if (!currentComparisonLeft || !state.users.some((user) => user.id === currentComparisonLeft)) {
        currentComparisonLeft = state.users[0].id;
      }
      comparisonLeftSelect.value = currentComparisonLeft;

      if (!currentComparisonRight || !state.users.some((user) => user.id === currentComparisonRight)) {
        currentComparisonRight = state.users[1]?.id || state.users[0].id;
      }
      comparisonRightSelect.value = currentComparisonRight;
    }
  }

  async function fetchState() {
    try {
      updateStatus('Syncing…');
      const [stateResponse, worldviewResponse] = await Promise.all([
        fetch('/api/state'),
        fetch('/api/worldview'),
      ]);
      if (!stateResponse.ok) throw new Error('Failed to fetch state');
      const stateData = await stateResponse.json();
      state.nodes = stateData.nodes || [];
      state.links = stateData.links || [];
      state.users = stateData.users || [];
      buildStateMaps();

      if (worldviewResponse.ok) {
        state.worldview = await worldviewResponse.json();
      }
      updateSelectors();
      renderCurrentView();
      updateStatus('Synced', true);
    } catch (error) {
      console.error(error);
      updateStatus('Offline');
    }
  }

  async function submitForm(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message);
    }
    return response.json();
  }

  function handleViewChange(event) {
    if (event.target.checked) {
      setView(event.target.value);
    }
  }

  function attachEventListeners() {
    document.querySelectorAll('input[name="view"]').forEach((radio) => {
      radio.addEventListener('change', handleViewChange);
    });

    document.querySelectorAll('.slider-group input[type="range"]').forEach((slider) => {
      slider.addEventListener('input', (event) => {
        const valueElement = event.target.closest('.slider-group').querySelector('.value');
        if (valueElement) {
          valueElement.textContent = Number(event.target.value).toFixed(2);
        }
      });
    });

    inventoryUserSelect?.addEventListener('change', (event) => {
      currentInventoryUser = event.target.value;
      renderInventoryView();
    });
    comparisonLeftSelect?.addEventListener('change', (event) => {
      currentComparisonLeft = event.target.value;
      renderComparisonView();
    });
    comparisonRightSelect?.addEventListener('change', (event) => {
      currentComparisonRight = event.target.value;
      renderComparisonView();
    });
    dimensionXSelect?.addEventListener('change', (event) => {
      currentDimensionX = Number(event.target.value);
      renderWorldviewView();
    });
    dimensionYSelect?.addEventListener('change', (event) => {
      currentDimensionY = Number(event.target.value);
      renderWorldviewView();
    });

    document.getElementById('ingest-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const feedUrl = form.feedUrl.value || null;
      const limit = Number(form.limit.value || 5);
      try {
        form.querySelector('button').disabled = true;
        await submitForm('/api/ingest', { feed_url: feedUrl, limit });
        await fetchState();
      } catch (error) {
        console.error(error);
        alert('Unable to ingest feed. See console for details.');
      } finally {
        form.querySelector('button').disabled = false;
      }
    });

    document.getElementById('idea-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const tags = form.tags.value
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean);
      const payload = {
        user_name: form.userName.value.trim(),
        title: form.title.value.trim(),
        summary: form.summary.value.trim(),
        tags,
        agreement: Number(form.agreement.value),
        confidence: Number(form.confidence.value),
        stance: form.stance.value,
        importance: Number(form.importance.value),
        link_target_id: form.linkTarget.value || null,
        link_type: form.linkType.value,
        link_weight: Number(form.linkWeight.value),
      };
      if (!payload.user_name || !payload.title || !payload.summary) {
        alert('Please fill in your name, title, and summary.');
        return;
      }
      try {
        form.querySelector('button').disabled = true;
        await submitForm('/api/ideas', payload);
        form.reset();
        await fetchState();
      } catch (error) {
        console.error(error);
        alert('Unable to add idea. See console for details.');
      } finally {
        form.querySelector('button').disabled = false;
      }
    });

    document.getElementById('opinion-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      if (!form.userName.value || !form.nodeId.value) {
        alert('Select both a user and a node to weight.');
        return;
      }
      const payload = {
        user_name: form.userName.value,
        node_id: form.nodeId.value,
        agreement: Number(form.agreement.value),
        confidence: Number(form.confidence.value),
        stance: form.stance.value,
        weight: Number(form.weight.value),
      };
      try {
        form.querySelector('button').disabled = true;
        await submitForm('/api/opinions', payload);
        await fetchState();
      } catch (error) {
        console.error(error);
        alert('Unable to save weighting. See console for details.');
      } finally {
        form.querySelector('button').disabled = false;
      }
    });
  }

  async function init() {
    attachEventListeners();
    await fetchState();
  }

  window.addEventListener('load', init);
})();
