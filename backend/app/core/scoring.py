"""
AI-анализ лидов: определение температуры, срочности, отдела,
рекомендации по персональному менеджеру.
"""
from datetime import datetime, timezone


# ────────────────────────────────────────────────────────────
# Эвристики оценки
# ────────────────────────────────────────────────────────────

def analyze_lead(
    niche: str | None = None,
    company_size: str | None = None,
    role: str | None = None,
    task_type: str | None = None,
    product_interest: str | None = None,
    budget: str | None = None,
    deadline: str | None = None,
    time_on_page: int = 0,
    clicks: int = 0,
    returns: int = 0,
) -> dict:
    """Анализирует заявку и возвращает результат:

    - score: 0-100 (чем выше, тем «горячее»)
    - temperature: "hot" | "warm" | "cold"
    - urgency: "high" | "medium" | "low"
    - department: какой отдел должен обработать
    - needs_personal_manager: стоит ли назначить персонального менеджера
    - recommendation: текстовая рекомендация
    """
    score = 0
    reasons = []

    # ── Бюджет ──
    budget_score = _score_budget(budget)
    score += budget_score
    if budget_score >= 25:
        reasons.append("высокий бюджет")

    # ── Сроки ──
    deadline_score = _score_deadline(deadline)
    score += deadline_score
    if deadline_score >= 20:
        reasons.append("срочные сроки")

    # ── Роль ──
    role_score = _score_role(role)
    score += role_score
    if role == "executive":
        reasons.append("решающее лицо")

    # ── Размер компании ──
    size_score = _score_company_size(company_size)
    score += size_score

    # ── Ниша ──
    niche_score = _score_niche(niche)
    score += niche_score

    # ── Продукт ──
    product_score = _score_product(product_interest)
    score += product_score

    # ── Поведение на странице ──
    behavior_score = _score_behavior(time_on_page, clicks, returns)
    score += behavior_score
    if behavior_score >= 15:
        reasons.append("активное поведение")

    # Нормализуем до 0-100
    score = min(100, max(0, score))

    # Температура
    if score >= 60:
        temperature = "hot"
    elif score >= 35:
        temperature = "warm"
    else:
        temperature = "cold"

    # Срочность
    urgency_score = deadline_score + behavior_score
    if urgency_score >= 30:
        urgency = "high"
    elif urgency_score >= 15:
        urgency = "medium"
    else:
        urgency = "low"

    # Отдел
    department = _determine_department(niche, task_type, product_interest)

    # Персональный менеджер
    needs_pm = score >= 55 and (role == "executive" or size_score >= 20)

    # Рекомендация
    if score >= 70:
        recommendation = (
            "Критически важный лид! "
            "Рекомендуется немедленная обработка в течение 1 часа. "
            "Назначить персонального менеджера."
            + (f" Приоритетные факторы: {', '.join(reasons)}." if reasons else "")
        )
    elif score >= 50:
        recommendation = (
            "Тёплый лид. "
            "Рекомендуется обработка в течение 24 часов. "
            "Рассмотреть назначение менеджера."
            + (f" Приоритетные факторы: {', '.join(reasons)}." if reasons else "")
        )
    elif score >= 30:
        recommendation = (
            "Лид средней температуры. "
            "Обработка в течение 48 часов. "
            "Достаточно стандартного follow-up."
        )
    else:
        recommendation = (
            "Холодный лид. "
            "Включить в автоматическую nurture-цепочку. "
            "Ручная обработка не требуется."
        )

    return {
        "score": score,
        "temperature": temperature,
        "urgency": urgency,
        "department": department,
        "needs_personal_manager": needs_pm,
        "recommendation": recommendation,
        "reasons": reasons,
    }


def _score_budget(budget: str | None) -> int:
    if not budget:
        return 5
    # Извлекаем числа из строки "5000–15000 ₽" или "100-300k"
    cleaned = budget.replace("–", "-").replace(" ", "").replace("₽", "").replace("р", "")
    parts = cleaned.split("-")
    try:
        max_val = float(parts[-1].replace("k", "000").replace("m", "000000"))
    except (ValueError, IndexError):
        return 5
    if max_val >= 500000:
        return 30
    elif max_val >= 200000:
        return 25
    elif max_val >= 50000:
        return 15
    return 5


def _score_deadline(deadline: str | None) -> int:
    if not deadline:
        return 5
    dl_lower = deadline.lower()
    if any(w in dl_lower for w in ["срочно", "urgent", "сегодня", "завтра"]):
        return 30
    if any(w in dl_lower for w in ["квартал", "месяц", "неделя", "soon"]):
        return 20
    if any(w in dl_lower for w in ["год", "long", "пока"]):
        return 5
    return 10


def _score_role(role: str | None) -> int:
    if role == "executive":
        return 25
    if role == "employee":
        return 10
    return 5


def _score_company_size(size: str | None) -> int:
    if size == "large":
        return 20
    if size == "medium":
        return 15
    if size == "small":
        return 10
    if size == "freelancer":
        return 5
    return 5


def _score_niche(niche: str | None) -> int:
    if not niche:
        return 5
    niche_lower = niche.lower()
    hot_niches = ["saa", "finan", "e-com", "e-commer", "маркет", "банки", "крипт"]
    cold_niches = ["студент", "учебный", "хобби"]
    for n in hot_niches:
        if n in niche_lower:
            return 20
    for n in cold_niches:
        if n in niche_lower:
            return 3
    return 10


def _score_product(product: str | None) -> int:
    if not product:
        return 5
    product_lower = product.lower()
    if any(w in product_lower for w in ["керам", "поликр", "полиров", "химчист"]):
        return 15
    return 10


def _score_behavior(time_on_page: int, clicks: int, returns: int) -> int:
    score = 0
    if time_on_page >= 120:
        score += 10
    elif time_on_page >= 60:
        score += 5
    if clicks >= 30:
        score += 10
    elif clicks >= 15:
        score += 5
    if returns >= 2:
        score += 10
    elif returns >= 1:
        score += 5
    return min(30, score)


def _determine_department(
    niche: str | None,
    task_type: str | None,
    product: str | None,
) -> str:
    if not task_type and not product:
        return "general"
    t = (task_type or "").lower()
    p = (product or "").lower()
    if any(w in t or w in p for w in ["маркетинг", "реклам", "seo", "трафик"]):
        return "marketing"
    if any(w in t or w in p for w in ["разраб", "разработ", "it", "saas", "автомат"]):
        return "development"
    if any(w in t or w in p for w in ["дизайн", "ui", "ux", "бренд"]):
        return "design"
    if any(w in p for w in ["керам", "полир", "химчист", "покраск"]):
        return "auto_service"
    if any(w in t or w in p for w in ["прод", "продаж", "logist"]):
        return "sales"
    return "general"