/* Seed Bayes Lab: portable offline controls and finite Bayesian arithmetic.
 * Do not insert historical probabilities here: all inputs are hypothetical.
 * This script uses Plotly that is embedded locally by the HTML exporter.
 */
(function (root) {
  'use strict';

  const TOL = 1e-13;
  const GROUPS = ['bayes', 'search'];
  const TABS = ['bayes', 'search', 'glossary'];
  const copy = state => ({ ...state });

  function finiteBayes(s) {
    const intent = s.prior_intent;
    const success = s.success_given_intent;
    const honest = 1 - intent;
    const failed = intent * (1 - success);
    const backdoor = intent * success;
    const h = honest * s.likelihood_honest;
    const f = failed * s.likelihood_failed;
    const b = backdoor * s.likelihood_succeeded;
    const evidence = h + f + b;
    if (!(evidence > 0)) {
      return { before: backdoor, after: null, intentAfter: null, delta: null, evidence };
    }
    return {
      before: backdoor,
      after: b / evidence,
      intentAfter: (f + b) / evidence,
      delta: b / evidence - backdoor,
      evidence
    };
  }

  function independentSearch(k, available, budget) {
    const q = Math.pow(2, -k);
    const attempts = Math.pow(2, Math.min(available, budget));
    return -Math.expm1(attempts * Math.log1p(-q));
  }

  function methodUpdate(s) {
    const t = s.know_restricted * independentSearch(
      s.rarity_bits, s.restricted_bits, s.compute_bits);
    const u = s.know_unrestricted * independentSearch(
      s.rarity_bits, s.unrestricted_bits, s.compute_bits);
    const a = s.prior_restricted;
    const rho = s.publish_failed;
    const publishedT = t + (1 - t) * rho;
    const publishedU = u + (1 - u) * rho;
    const published = a * publishedT + (1 - a) * publishedU;
    const before = published > 0 ? (a * t + (1 - a) * u) / published : null;
    const after = publishedT > 0 && a > 0 ? t / publishedT : null;
    const delta = before === null || after === null ? null :
      rho * (1 - a) * (t - u) / (publishedT * published);
    return { before, after, delta, restrictedSuccess: t, unrestrictedSuccess: u };
  }

  function direction(delta) {
    if (delta === null || !Number.isFinite(delta)) return 'undefined';
    if (delta < -TOL) return 'decrease';
    if (delta > TOL) return 'increase';
    return 'unchanged';
  }

  function formatter(delta) {
    if (delta === null || !Number.isFinite(delta)) return 'undefined';
    if (direction(delta) === 'unchanged') return '\u22480 pp';
    const abs = Math.abs(delta * 100);
    const numeric = abs < 0.001 ? abs.toPrecision(2) : abs.toFixed(2);
    return (delta > 0 ? '\u2197 +' : '\u2198 \u2212') + numeric + ' pp';
  }

  function percent(p) {
    return p === null || !Number.isFinite(p) ? 'undefined' :
      (100 * p).toFixed(p !== 0 && p < 0.000001 ? 7 : 2) + '%';
  }

  function sweep(s, spec) {
    const evaluate = spec.group === 'bayes' ? finiteBayes : methodUpdate;
    const current = evaluate(s).delta;
    let minimum = null, maximum = null;
    let left = null, right = null, leftPosterior = null, rightPosterior = null;
    let undefinedCount = 0;
    const directions = new Set();
    const count = Math.round((spec.max - spec.min) / spec.step);
    for (let i = 0; i <= count; i += 1) {
      const probe = copy(s);
      probe[spec.key] = Number((spec.min + i * spec.step).toFixed(9));
      const result = evaluate(probe);
      const delta = result.delta;
      if (i === 0) { left = delta; leftPosterior = result.after; }
      if (i === count) { right = delta; rightPosterior = result.after; }
      if (delta === null) { undefinedCount += 1; continue; }
      directions.add(direction(delta));
      minimum = minimum === null ? delta : Math.min(minimum, delta);
      maximum = maximum === null ? delta : Math.max(maximum, delta);
    }
    const present = direction(current);
    const reverse = (present === 'decrease' && directions.has('increase')) ||
      (present === 'increase' && directions.has('decrease'));
    const equality = ['increase','decrease'].includes(present) && directions.has('unchanged');
    let status;
    if (present === 'undefined') status = 'Current conditioning undefined';
    else if (reverse) status = 'CAN REVERSE';
    else if (present === 'unchanged') {
      if (directions.has('increase') && directions.has('decrease')) status = 'Can move \u2197 or \u2198';
      else if (directions.has('increase')) status = 'Can increase';
      else if (directions.has('decrease')) status = 'Can decrease';
      else status = 'Remains unchanged';
    } else if (equality) status = 'Can reach equality, not reverse';
    else status = 'Cannot reverse';
    // Endpoint updates are evaluated with this dial pinned to MIN or MAX.
    // They cannot depend on the same dial's live position, but may depend on
    // every other dial. Do NOT subtract the current posterior here.
    return { left, right, leftPosterior, rightPosterior,
      minimum, maximum, undefinedCount, directions,
      current, present, reverse, equality, status };
  }

  function createText(tag, css, text) {
    const node = document.createElement(tag);
    if (css) node.className = css;
    node.textContent = text;
    return node;
  }

  function renderControls(config, values, onInput) {
    for (const group of GROUPS) {
      const target = document.getElementById(group + '-controls');
      target.replaceChildren();
      for (const spec of config.specs.filter(item => item.group === group)) {
        const wrap = createText('div', 'dial', '');
        wrap.dataset.key = spec.key;
        const head = createText('div', 'dial-header', '');
        const label = createText('label', '', spec.label);
        label.htmlFor = 'slider-' + spec.key;
        const value = createText('strong', 'dial-value', '');
        value.id = 'value-' + spec.key;
        head.append(label, value);
        const slider = document.createElement('input');
        slider.id = 'slider-' + spec.key;
        slider.type = 'range';
        slider.min = String(spec.min);
        slider.max = String(spec.max);
        slider.step = String(spec.step);
        slider.value = String(values[spec.key]);
        slider.setAttribute('aria-label', spec.label);
        slider.addEventListener('input', () => {
          values[spec.key] = Number(slider.value);
          onInput(group);
        });
        const rail = createText('div', 'dial-rail', '');
        const left = createText('div', 'dial-extreme', '');
        left.id = 'left-' + spec.key;
        const sliderWrap = createText('div', 'dial-slider-wrap', '');
        sliderWrap.append(slider);
        const right = createText('div', 'dial-extreme', '');
        right.id = 'right-' + spec.key;
        rail.append(left, sliderWrap, right);
        const statusRow = createText('div', 'dial-meta', '');
        const status = createText('span', 'dial-status', '');
        status.id = 'status-' + spec.key;
        const range = createText('span', 'dial-range', '');
        range.id = 'range-' + spec.key;
        statusRow.append(status, range);
        wrap.append(head, rail, statusRow);
        target.appendChild(wrap);
      }
    }
  }

  function renderExtreme(targetId, edgeLabel, point, posterior, evidenceDelta, group) {
    const element = document.getElementById(targetId);
    const sign = direction(evidenceDelta);
    const symbol = sign === 'increase' ? '\u2197' : sign === 'decrease' ? '\u2198' :
      sign === 'unchanged' ? '\u2192' : '?';
    const numeric = evidenceDelta === null ? 'undefined' :
      sign === 'unchanged' ? '\u22480 pp' :
      (evidenceDelta > 0 ? '+' : '\u2212') +
      (Math.abs(evidenceDelta * 100) < 0.001 ? Math.abs(evidenceDelta * 100).toPrecision(2) :
       Math.abs(evidenceDelta * 100).toFixed(2)) + ' pp';
    const title = createText('div', 'extreme-label', edgeLabel + ' ' + point);
    const content = createText('div', 'extreme-main', '');
    const icon = createText('span', 'extreme-icon', symbol);
    icon.setAttribute('aria-hidden', 'true');
    const amount = createText('strong', 'extreme-number', numeric);
    content.append(icon, amount);
    const afterName = group === 'bayes' ? 'P(B | E)' : 'P(B | J,T)';
    const detail = createText('div', 'extreme-posterior', afterName + ' ' + percent(posterior));
    element.className = 'dial-extreme ' + sign;
    element.setAttribute('aria-label', edgeLabel + ' setting ' + point +
      ', evidence update at endpoint (posterior minus prior): ' +
      formatter(evidenceDelta) + ', endpoint ' + afterName + ': ' + percent(posterior));
    element.replaceChildren(title, content, detail);
  }

  function renderSweepIndicators(config, values) {
    for (const group of GROUPS) {
      const specs = config.specs.filter(item => item.group === group);
      let reversible = 0;
      const reversibleNames = [];
      for (const spec of specs) {
        const sensitivity = sweep(values, spec);
        const isBit = spec.step >= 1;
        document.getElementById('value-' + spec.key).textContent = isBit ?
          values[spec.key] + ' bits' : Number(values[spec.key]).toFixed(2);
        renderExtreme('left-' + spec.key, 'MIN', spec.min,
          sensitivity.leftPosterior, sensitivity.left, group);
        renderExtreme('right-' + spec.key, 'MAX', spec.max,
          sensitivity.rightPosterior, sensitivity.right, group);
        const status = document.getElementById('status-' + spec.key);
        status.textContent = sensitivity.status;
        status.className = 'dial-status ' + (sensitivity.reverse ? 'flip' :
          sensitivity.equality ? 'equality' : 'fixed');
        const range = document.getElementById('range-' + spec.key);
        range.textContent = 'Update \u0394 range: ' + formatter(sensitivity.minimum) +
          ' to ' + formatter(sensitivity.maximum) +
          (sensitivity.undefinedCount ?
          ' \u00b7 ' + sensitivity.undefinedCount + ' undefined setting(s)' : '');
        if (sensitivity.reverse) {
          reversible += 1;
          reversibleNames.push(spec.label);
        }
      }
      const current = direction(group === 'bayes' ? finiteBayes(values).delta : methodUpdate(values).delta);
      document.getElementById(group + '-flip-summary').textContent =
        'Current: ' + current + '. ' + reversible + ' of ' + specs.length +
        ' dials can reverse the direction individually' +
        (reversibleNames.length ? ': ' + reversibleNames.join('; ') + '.' : '.');
    }
  }

  const CHART_OPTIONS = { responsive: true, displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d','select2d'] };

  function lineFigure(s) {
    const xs = Array.from({length: 101}, (_, i) => i / 100);
    const ys = xs.map(e => finiteBayes({...s, likelihood_succeeded: e}).after);
    const now = finiteBayes(s);
    const traces = [
      {x: xs, y: ys, name: 'P(B | E)', type:'scatter', mode:'lines',
       line:{color:'#285aa3',width:3}},
      {x: [0,1], y:[now.before,now.before], name:'P(B) before E', type:'scatter',
       mode:'lines',line:{dash:'dash',color:'#8c93a0',width:2}},
      {x:[s.likelihood_succeeded],y:[now.after],name:'Current assumptions',
       type:'scatter',mode:'markers',marker:{size:11,color:'#c05d33'}}
    ];
    const layout = {title: {text: 'Bayesian evidence sensitivity', font:{size:16}},
      xaxis: {title: 'P(E | successful backdoor)',range:[0,1]},
      yaxis: {title: 'P(B | E)',range:[0,1.02],tickformat:'.0%'},
      margin:{l:65,r:14,t:45,b:65},
      legend:{orientation:'h',y:-0.3},paper_bgcolor:'#fff',plot_bgcolor:'#fff'};
    return [traces,layout];
  }

  function heatmapFigure(s) {
    const v = Array.from({length: 41}, (_, i) => i/40);
    const z = v.map(lB => v.map(lF => finiteBayes({
      ...s, likelihood_failed:lF, likelihood_succeeded:lB
    }).delta));
    const magnitudes = z.flat().filter(x=>x!==null).map(x=>Math.abs(x));
    const lim = Math.max(...magnitudes,1e-10);
    const traces = [{x:v,y:v,z:z.map(row=>row.map(x=>x===null?null:x*100)),
      type:'heatmap',colorscale:'RdBu',reversescale:true,
      zmin:-lim*100,zmax:lim*100,
      colorbar:{title:'\u0394 pp'},
      hovertemplate:'P(E | failed): %{x:.2f}<br>P(E | success): %{y:.2f}<br>\u0394: %{z:+.3f} pp<extra></extra>'}];
    const layout = {title:{text:'Sign of the update',font:{size:16}},
      xaxis:{title:'P(E | failed attempt)'},yaxis:{title:'P(E | backdoor)'},
      margin:{l:65,r:12,t:45,b:65},paper_bgcolor:'#fff',plot_bgcolor:'#fff'};
    return [traces,layout];
  }

  function searchFigure(s) {
    const xs = Array.from({length:151},(_,i)=>5+i/2);
    const comparisons = xs.map(k=>methodUpdate({...s,rarity_bits:k}));
    const traces = [
      ['P(success | T)','restrictedSuccess','#26758a','solid'],
      ['P(success | U)','unrestrictedSuccess','#b58931','solid'],
      ['P(B | published)','before','#8995a5','dot'],
      ['P(B | published, T)','after','#b85552','dash']
    ].map(([name,key,color,dash])=>({
      x:xs,y:comparisons.map(row=>row[key]),name,
      type:'scatter',mode:'lines',line:{width:2.5,color,dash}
    }));
    const now=methodUpdate(s);
    traces.push({x:[s.rarity_bits],y:[now.after],
      name:'Current P(B | published,T)',type:'scatter',mode:'markers',
      marker:{size:10,color:'#b85552'}});
    const layout={title:{text:'Method and publication sensitivity',font:{size:16}},
      xaxis:{title:'Rarity k (q = 2^-k)',range:[5,80]},
      yaxis:{title:'Probability',tickformat:'.0%',range:[0,1.02]},
      margin:{l:65,r:12,t:45,b:80},legend:{orientation:'h',y:-0.3},
      paper_bgcolor:'#fff',plot_bgcolor:'#fff'};
    return [traces,layout];
  }

  function renderSummary(values, group) {
    const result = group === 'bayes' ? finiteBayes(values) : methodUpdate(values);
    const prior = document.getElementById(group + '-before');
    const after = document.getElementById(group + '-after');
    const delta = document.getElementById(group + '-delta');
    prior.textContent = percent(result.before);
    after.textContent = percent(result.after);
    delta.textContent = formatter(result.delta);
    delta.dataset.direction = direction(result.delta);
    if (group === 'bayes') {
      document.getElementById('bayes-intent-after').textContent = percent(result.intentAfter);
    }
  }

  function mount(config) {
    const state = copy(config.defaults);
    let active = 'bayes';
    let frame = false;

    function drawPlots() {
      frame = false;
      if (!root.Plotly) return;
      if (active === 'bayes') {
        const [line, layout] = lineFigure(state);
        const [map, mapLayout] = heatmapFigure(state);
        root.Plotly.react('bayes-line',line,layout,CHART_OPTIONS);
        root.Plotly.react('bayes-heatmap',map,mapLayout,CHART_OPTIONS);
      } else if (active === 'search') {
        const [curves,layout] = searchFigure(state);
        root.Plotly.react('search-curves',curves,layout,CHART_OPTIONS);
      }
    }

    function renderAll() {
      renderSweepIndicators(config, state);
      for (const group of GROUPS) renderSummary(state,group);
      if (!frame) { frame = true; root.requestAnimationFrame(drawPlots); }
    }

    renderControls(config, state, renderAll);
    for (const name of TABS) {
      const tab = document.getElementById('tab-' + name);
      tab.addEventListener('click',()=>{
        active = name;
        for (const section of TABS) {
          document.getElementById('panel-' + section).hidden = section !== name;
          document.getElementById('tab-' + section).setAttribute('aria-selected',String(section===name));
        }
        renderAll();
      });
    }
    document.getElementById('reset-all').addEventListener('click',()=>{
      Object.assign(state,copy(config.defaults));
      for (const spec of config.specs) {
        document.getElementById('slider-' + spec.key).value = String(state[spec.key]);
      }
      renderAll();
    });
    renderAll();
    return state;
  }

  root.SeedBayesOffline = {
    finiteBayes, methodUpdate, independentSearch, direction, formatter, sweep, mount
  };
})(typeof globalThis !== 'undefined' ? globalThis : this);
