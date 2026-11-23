const state = { products: [], cart: new Map(), filter: "all", query: "" };
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char]));
const currency = (cents) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 2,
}).format((Number(cents) || 0) / 100);

function iconFor(product) {
  const text = `${product.name} ${product.sku}`.toLowerCase();
  if (text.includes("mug") || text.includes("cup") || text.includes("coffee")) return "☕";
  if (text.includes("tee") || text.includes("shirt") || text.includes("wear")) return "👕";
  if (text.includes("book") || text.includes("paper")) return "📚";
  if (text.includes("plant") || text.includes("flower")) return "🪴";
  return "✳";
}

async function loadProducts() {
  const message = $("#catalog-message");
  message.hidden = true;
  $("#product-grid").innerHTML = "";
  try {
    const response = await fetch("/api/products", { headers: { Accept: "application/json" } });
    const products = await response.json();
    if (!response.ok || !Array.isArray(products)) throw new Error(products.error || "Could not load products.");
    state.products = products;
    renderCatalog();
    renderCart();
  } catch (error) {
    message.hidden = false;
    message.innerHTML = `<strong>We couldn’t reach the catalog.</strong>${escapeHtml(error.message)} Check that the Tillpoint server is running, then refresh.`;
  }
}

function renderCatalog() {
  const grid = $("#product-grid");
  const query = state.query.trim().toLowerCase();
  const products = state.products.filter((product) => {
    const matchesQuery = `${product.name} ${product.sku}`.toLowerCase().includes(query);
    const matchesFilter = state.filter === "all" || Number(product.stock) > 0;
    return matchesQuery && matchesFilter;
  });
  const totalUnits = state.products.reduce((sum, product) => sum + Number(product.stock || 0), 0);
  $("#product-count").textContent = state.products.length;
  $("#unit-count").textContent = totalUnits;

  if (!products.length) {
    grid.innerHTML = "";
    const message = $("#catalog-message");
    message.hidden = false;
    message.innerHTML = state.products.length
      ? "<strong>No matches this time.</strong>Try another search or switch the stock filter."
      : "<strong>Your catalog is ready for its first product.</strong>Add products to the Tillpoint database and they’ll appear here.";
    return;
  }
  $("#catalog-message").hidden = true;
  grid.innerHTML = products.map((product, index) => {
    const stock = Number(product.stock) || 0;
    const stockClass = stock === 0 ? "out-stock" : stock < 4 ? "low-stock" : "";
    const stockLabel = stock === 0 ? "Sold out" : stock < 4 ? `${stock} left` : `${stock} in stock`;
    return `<article class="product-card">
      <div class="product-card-top">
        <div class="product-visual visual-${["a", "b", "c", "d"][index % 4]}" aria-hidden="true">${iconFor(product)}</div>
        <span class="stock-tag ${stockClass}">${stockLabel}</span>
      </div>
      <div class="product-info">
        <div class="product-copy">
          <div class="product-name" title="${escapeHtml(product.name)}">${escapeHtml(product.name)}</div>
          <div class="product-sku">${escapeHtml(product.sku)}</div>
          <div class="product-price">${currency(product.price_cents)}</div>
        </div>
        <button class="add-button" type="button" data-add="${escapeHtml(product.sku)}" aria-label="Add ${escapeHtml(product.name)} to order" ${stock <= 0 ? "disabled" : ""}>+</button>
      </div>
    </article>`;
  }).join("");
}

function renderCart() {
  const container = $("#cart-items");
  const entries = [...state.cart.values()];
  const count = entries.reduce((sum, item) => sum + item.qty, 0);
  const subtotal = entries.reduce((sum, item) => sum + item.qty * Number(item.product.price_cents), 0);
  $("#cart-count").textContent = `${count} ${count === 1 ? "item" : "items"}`;
  $("#subtotal").textContent = currency(subtotal);
  $("#checkout").disabled = count === 0;

  if (!entries.length) {
    container.innerHTML = '<div class="cart-empty"><span class="empty-basket" aria-hidden="true">＋</span><p>Your basket is waiting.</p><small>Add a product to get started.</small></div>';
    return;
  }
  container.innerHTML = entries.map(({ product, qty }) => `<div class="cart-row">
    <div><div class="cart-row-name">${escapeHtml(product.name)}</div><div class="cart-row-sub">${currency(product.price_cents)} each</div></div>
    <div class="quantity-control" aria-label="Quantity for ${escapeHtml(product.name)}">
      <button type="button" data-qty="${escapeHtml(product.sku)}" data-change="-1" aria-label="Remove one">−</button>
      <span>${qty}</span>
      <button type="button" data-qty="${escapeHtml(product.sku)}" data-change="1" aria-label="Add one" ${qty >= Number(product.stock) ? "disabled" : ""}>+</button>
    </div>
  </div>`).join("");
}

function addToCart(sku, delta = 1) {
  const product = state.products.find((item) => item.sku === sku);
  if (!product) return;
  const current = state.cart.get(sku)?.qty || 0;
  const next = Math.max(0, Math.min(Number(product.stock), current + delta));
  if (next === 0) state.cart.delete(sku);
  else state.cart.set(sku, { product, qty: next });
  $("#order-message").textContent = "";
  renderCart();
}

async function placeOrder() {
  const customer = $("#customer").value.trim();
  const items = [...state.cart.values()].map(({ product, qty }) => ({ sku: product.sku, qty }));
  const message = $("#order-message");
  message.classList.remove("is-error");
  if (!customer) {
    message.textContent = "Add the customer’s name to continue.";
    message.classList.add("is-error");
    $("#customer").focus();
    return;
  }
  if (!items.length) return;

  const button = $("#checkout");
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Placing order…";
  try {
    const payload = {
      customer,
      items,
      region: $("#region").value,
      coupon: $("#coupon").value.trim() || null,
    };
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const order = await response.json();
    if (!response.ok) throw new Error(order.error || "The order could not be placed.");
    message.textContent = `Order #${order.id} created · ${currency(order.total_cents)} total`;
    state.cart.clear();
    $("#customer").value = "";
    $("#coupon").value = "";
    renderCart();
    await loadProducts();
  } catch (error) {
    message.textContent = error.message;
    message.classList.add("is-error");
  } finally {
    button.querySelector("span:first-child").textContent = "Place order";
    renderCart();
  }
}

$("#product-grid").addEventListener("click", (event) => {
  const button = event.target.closest("[data-add]");
  if (button) addToCart(button.dataset.add);
});
$("#cart-items").addEventListener("click", (event) => {
  const button = event.target.closest("[data-qty]");
  if (button) addToCart(button.dataset.qty, Number(button.dataset.change));
});
$("#search").addEventListener("input", (event) => { state.query = event.target.value; renderCatalog(); });
$(".filter-pills").addEventListener("click", (event) => {
  const button = event.target.closest("[data-filter]");
  if (!button) return;
  state.filter = button.dataset.filter;
  document.querySelectorAll(".filter-pill").forEach((pill) => pill.classList.toggle("is-active", pill === button));
  renderCatalog();
});
$("#refresh-button").addEventListener("click", loadProducts);
$("#checkout").addEventListener("click", placeOrder);
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    $("#search").focus();
  }
});

loadProducts();
