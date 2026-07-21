/* Prompt detail page: handles "Buy now" and star-rating review submission. */
(function () {
  const buyBtn = document.getElementById("buy-btn");
  const buyMsg = document.getElementById("buy-msg");

  if (buyBtn) {
    buyBtn.addEventListener("click", async function () {
      const promptId = buyBtn.dataset.promptId;
      buyBtn.disabled = true;
      buyBtn.textContent = "Processing…";
      buyMsg.textContent = "";
      buyMsg.className = "msg-inline";
      try {
        await Api.post(`/api/prompts/${promptId}/purchase`, {});
        buyMsg.textContent = "Purchase complete! Reloading…";
        buyMsg.classList.add("success");
        setTimeout(function () { window.location.reload(); }, 700);
      } catch (err) {
        buyBtn.disabled = false;
        buyBtn.textContent = "Buy now";
        buyMsg.textContent = err.message;
        buyMsg.classList.add("error");
      }
    });
  }

  // Star rating widget
  const starInput = document.getElementById("star-input");
  const ratingValue = document.getElementById("rating-value");
  if (starInput) {
    const stars = Array.from(starInput.querySelectorAll("span"));
    function paint(value) {
      stars.forEach(function (s) {
        s.classList.toggle("active", Number(s.dataset.value) <= value);
      });
    }
    stars.forEach(function (s) {
      s.addEventListener("mouseenter", function () { paint(Number(s.dataset.value)); });
      s.addEventListener("click", function () {
        ratingValue.value = s.dataset.value;
        paint(Number(s.dataset.value));
      });
    });
    starInput.addEventListener("mouseleave", function () {
      paint(Number(ratingValue.value));
    });
  }

  const submitReviewBtn = document.getElementById("submit-review-btn");
  if (submitReviewBtn) {
    submitReviewBtn.addEventListener("click", async function () {
      const promptId = submitReviewBtn.dataset.promptId;
      const rating = Number(document.getElementById("rating-value").value);
      const comment = document.getElementById("review-comment").value.trim();
      const msg = document.getElementById("review-msg");
      msg.textContent = "";
      msg.className = "msg-inline";

      if (!rating) {
        msg.textContent = "Please select a star rating.";
        msg.classList.add("error");
        return;
      }

      submitReviewBtn.disabled = true;
      submitReviewBtn.textContent = "Submitting…";
      try {
        await Api.post(`/api/prompts/${promptId}/reviews`, { rating, comment });
        msg.textContent = "Thanks for your review! Reloading…";
        msg.classList.add("success");
        setTimeout(function () { window.location.reload(); }, 700);
      } catch (err) {
        submitReviewBtn.disabled = false;
        submitReviewBtn.textContent = "Submit review";
        msg.textContent = err.message;
        msg.classList.add("error");
      }
    });
  }
})();
