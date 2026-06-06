//###################################################################################
// (1) ADMIN CARD STACK ORDER V1
//###################################################################################
(function registerAdminCardStackOrderV1() {
  "use strict";

  const ROLE_PRIORITY_V1 = Object.freeze({
    tabs: 10,
    create: 20,
    edit: 30,
    active: 40,
    inactive: 50
  });

  //###################################################################################
  // (2) HELPERS
  //###################################################################################

  function normalizeCardStackTokenV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function getRolePriorityV1(cardRole) {
    const normalizedRole = normalizeCardStackTokenV1(cardRole);
    return Object.prototype.hasOwnProperty.call(ROLE_PRIORITY_V1, normalizedRole)
      ? ROLE_PRIORITY_V1[normalizedRole]
      : 999;
  }

  function sortCardsByDomOrderV1(cards) {
    return cards.slice().sort(function (leftCard, rightCard) {
      if (leftCard === rightCard) {
        return 0;
      }

      const comparePosition = leftCard.compareDocumentPosition(rightCard);
      if (comparePosition & Node.DOCUMENT_POSITION_FOLLOWING) {
        return -1;
      }

      if (comparePosition & Node.DOCUMENT_POSITION_PRECEDING) {
        return 1;
      }

      return 0;
    });
  }

  function buildDesiredOrderV1(cards) {
    const domOrderedCards = sortCardsByDomOrderV1(cards);
    const domOrderIndex = new Map();

    domOrderedCards.forEach(function (card, index) {
      domOrderIndex.set(card, index);
    });

    return cards.slice().sort(function (leftCard, rightCard) {
      const priorityDiff =
        getRolePriorityV1(leftCard.getAttribute("data-admin-card-role")) -
        getRolePriorityV1(rightCard.getAttribute("data-admin-card-role"));

      if (priorityDiff !== 0) {
        return priorityDiff;
      }

      return (domOrderIndex.get(leftCard) || 0) - (domOrderIndex.get(rightCard) || 0);
    });
  }

  function buildGroupRegistryV1() {
    const registry = new Map();

    document.querySelectorAll("[data-admin-card-group][data-admin-card-role]").forEach(function (card) {
      const parent = card.parentElement;
      const groupKey = normalizeCardStackTokenV1(card.getAttribute("data-admin-card-group"));

      if (!parent || !groupKey) {
        return;
      }

      let parentGroups = registry.get(parent);
      if (!parentGroups) {
        parentGroups = new Map();
        registry.set(parent, parentGroups);
      }

      const cards = parentGroups.get(groupKey) || [];
      cards.push(card);
      parentGroups.set(groupKey, cards);
    });

    return registry;
  }

  function reorderCardGroupV1(cards) {
    if (!Array.isArray(cards) || cards.length < 2) {
      return;
    }

    const domOrderedCards = sortCardsByDomOrderV1(cards);
    const desiredCards = buildDesiredOrderV1(cards);
    const firstDomCard = domOrderedCards[0];

    if (!firstDomCard || !firstDomCard.parentElement) {
      return;
    }

    let insertionAnchor = firstDomCard;

    desiredCards.forEach(function (card, index) {
      if (index === 0) {
        if (card !== firstDomCard) {
          firstDomCard.insertAdjacentElement("beforebegin", card);
        }

        insertionAnchor = card;
        return;
      }

      if (insertionAnchor.nextElementSibling !== card) {
        insertionAnchor.insertAdjacentElement("afterend", card);
      }

      insertionAnchor = card;
    });
  }

  //###################################################################################
  // (3) APPLY ORDER
  //###################################################################################

  function applyAdminCardStackOrderV1() {
    const registry = buildGroupRegistryV1();

    registry.forEach(function (parentGroups) {
      parentGroups.forEach(function (cards) {
        reorderCardGroupV1(cards);
      });
    });
  }

  //###################################################################################
  // (4) INIT
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyAdminCardStackOrderV1);
  } else {
    applyAdminCardStackOrderV1();
  }

  window.addEventListener("load", applyAdminCardStackOrderV1);
  window.addEventListener("pageshow", applyAdminCardStackOrderV1);
  window.addEventListener("appverbo:admin-card-stack-order-v1", applyAdminCardStackOrderV1);

  window.setTimeout(applyAdminCardStackOrderV1, 80);
  window.setTimeout(applyAdminCardStackOrderV1, 250);
  window.setTimeout(applyAdminCardStackOrderV1, 800);
})();
