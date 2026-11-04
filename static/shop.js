(function () {
  const toast = document.getElementById('toast');
  const badge = document.getElementById('cart-badge');
  let timer;
  function say(msg, bad) {
    if (!toast) return;
    toast.textContent = msg; toast.classList.toggle('bad', !!bad); toast.classList.add('on');
    clearTimeout(timer); timer = setTimeout(() => toast.classList.remove('on'), 2600);
  }
  async function add(pid) {
    const fd = new FormData(); fd.append('pid', pid); fd.append('qty', 1);
    try {
      const r = await fetch('/carrinho/add', { method: 'POST', body: fd });
      const d = await r.json();
      if (d.ok && badge) { badge.textContent = d.count; badge.hidden = false; }
      say(d.msg, !d.ok);
    } catch (e) { say('Não foi possível adicionar. Tente de novo.', true); }
  }

  document.querySelectorAll('[data-add]').forEach(b => b.addEventListener('click', e => {
    e.stopPropagation(); add(b.dataset.add);
  }));

  const dlg = document.getElementById('pop');
  if (!dlg) return;
  const set = (id, t) => document.getElementById(id).textContent = t;
  let current = null;
  document.querySelectorAll('.card').forEach(card => card.addEventListener('click', () => {
    const d = card.dataset; current = d.id;
    document.getElementById('pop-vis').innerHTML = card.querySelector('.thumb').innerHTML;
    set('pop-cat', d.cat); set('pop-name', d.name); set('pop-desc', d.desc); set('pop-price', d.price);
    set('pop-stock', +d.stock > 0 ? 'Em estoque: ' + d.stock + ' un' : 'Indisponível');
    document.getElementById('pop-add').disabled = +d.stock < 1;
    dlg.showModal();
  }));
  document.getElementById('pop-add').onclick = () => { add(current); dlg.close(); };
  document.getElementById('pop-close').onclick = () => dlg.close();
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
})();
