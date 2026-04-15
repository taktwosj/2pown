import csv
import datetime
from collections import Counter
from html import escape
from pathlib import Path


REPORT_TYPE_OPTIONS = {
    "1": ("recent", "최근 접수 운영리포트"),
    "2": ("progress", "현재 진행상태 리포트"),
}

STATUS_PRIORITY = [
    "긴급관리",
    "기표예정",
    "자서완료",
    "진행보류",
    "신규상담",
    "기표완료",
]


def _send_report(bot, chat_id, report):
    if len(report) <= 4000:
        bot.send_message(chat_id, report, parse_mode="HTML")
        return

    chunk = ""
    for line in report.split("\n"):
        next_chunk = f"{chunk}\n{line}" if chunk else line
        if len(next_chunk) > 3900:
            if chunk:
                bot.send_message(chat_id, chunk, parse_mode="HTML")
            chunk = line
        else:
            chunk = next_chunk
    if chunk:
        bot.send_message(chat_id, chunk, parse_mode="HTML")


def _parse_iso_date(value):
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return datetime.date.fromisoformat(text)
    except Exception:
        return None


def _resolve_flow_summary_csv(base_dir):
    candidates = [
        Path(base_dir) / "projects" / "ivwith" / "고객흐름_요약.csv",
        Path(base_dir) / "ivwith" / "고객흐름_요약.csv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _normalize_loan(value):
    text = str(value or "").strip().replace(",", "")
    return text or "-"


def _normalize_phone(row):
    return str(row.get("대표연락처") or row.get("현재신용정보연락처") or "").strip() or "-"


def _normalize_week(row):
    return str(row.get("지속관리주차") or "").strip() or "-"


def _normalize_status(row):
    return str(row.get("고객상태필터") or "").strip() or "미분류"


def _normalize_bank(row):
    return str(row.get("현재은행") or "").strip() or "-"


def _normalize_name(row):
    return str(row.get("신청인") or "").strip() or "-"


def _normalize_note(row):
    text = str(row.get("현재메모") or row.get("비고") or "").strip()
    if not text:
        return ""
    return " ".join(text.split())


def format_report_type_menu():
    lines = [
        "<b>📋 ivwith 운영리포트</b>",
        "",
        "1. 최근 접수 운영리포트",
        "2. 현재 진행상태 리포트",
        "",
        "번호를 입력하세요. (0: 처음으로)",
    ]
    return "\n".join(lines)


def parse_report_type_selection(text):
    return REPORT_TYPE_OPTIONS.get(str(text or "").strip())


def get_report_type_label(report_type):
    for _, (key, label) in REPORT_TYPE_OPTIONS.items():
        if key == report_type:
            return label
    return "ivwith 리포트"


def format_sales_menu_for_report(report_label, sales_list):
    lines = [f"<b>📋 {escape(report_label)}</b>", "", "<b>영업자 선택:</b>"]
    for idx, (_, display) in enumerate(sales_list, 1):
        lines.append(f"  {idx}. {escape(display)}")
    lines.append("")
    lines.append("번호를 입력하세요. (0: 처음으로)")
    return "\n".join(lines)


def format_weeks_menu_for_report(report_label, sales_display):
    return (
        f"<b>📋 {escape(report_label)} / {escape(sales_display)} 기간 선택:</b>\n"
        "  1. 최근 1주\n"
        "  2. 최근 2주\n"
        "  3. 최근 3주\n"
        "  4. 최근 4주\n"
        "  5. 최근 5주\n"
        "  6. 최근 6주\n"
        "  7. 최근 7주\n"
        "  8. 최근 8주\n"
        "\n번호를 입력하세요. (0: 처음으로)"
    )


def parse_sales_selection(text, sales_list):
    try:
        idx = int(str(text or "").strip()) - 1
    except Exception:
        return None
    if 0 <= idx < len(sales_list):
        return sales_list[idx]
    return None


def parse_weeks_selection(text, week_options):
    return week_options.get(str(text or "").strip())


def clear_pending_sales_report(state):
    state["pending_ivwith_report_type"] = ""
    state["pending_ivwith_sales_key"] = ""
    state["pending_ivwith_sales_display"] = ""


def handle_state_40(
    *,
    bot,
    message,
    text,
    state,
    sales_list,
    show_list,
):
    choice = str(text or "").strip()
    if choice in {"0", "00", "취소"}:
        clear_pending_sales_report(state)
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True

    report_type = state.get("pending_ivwith_report_type") or ""
    if not report_type:
        selected = parse_report_type_selection(choice)
        if not selected:
            bot.send_message(message.chat.id, format_report_type_menu(), parse_mode="HTML")
            return True
        report_key, report_label = selected
        state["pending_ivwith_report_type"] = report_key
        bot.send_message(
            message.chat.id,
            format_sales_menu_for_report(report_label, sales_list),
            parse_mode="HTML",
        )
        return True

    selected_sales = parse_sales_selection(choice, sales_list)
    if not selected_sales:
        bot.send_message(message.chat.id, "번호를 다시 입력해주세요.")
        return True

    state["pending_ivwith_sales_key"], state["pending_ivwith_sales_display"] = selected_sales
    state["user_state"] = 41
    report_label = get_report_type_label(report_type)
    bot.send_message(
        message.chat.id,
        format_weeks_menu_for_report(report_label, state["pending_ivwith_sales_display"]),
        parse_mode="HTML",
    )
    return True


def handle_state_41(
    *,
    bot,
    message,
    text,
    state,
    week_options,
    start_background_task,
    show_list,
    build_customer_report,
    base_dir,
):
    choice = str(text or "").strip()
    if choice in {"0", "00", "취소"}:
        clear_pending_sales_report(state)
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True

    weeks = parse_weeks_selection(choice, week_options)
    if not weeks:
        bot.send_message(message.chat.id, "번호를 다시 입력해주세요 (1~8).")
        return True

    report_type = state.get("pending_ivwith_report_type") or "recent"
    sales_key = state.get("pending_ivwith_sales_key") or ""
    sales_display = state.get("pending_ivwith_sales_display") or ""
    report_label = get_report_type_label(report_type)

    clear_pending_sales_report(state)
    state["user_state"] = 0
    bot.send_message(
        message.chat.id,
        f"⏳ {sales_display} {report_label} 최근 {weeks // 7}주 조회를 백그라운드로 시작했습니다.",
    )
    start_background_task(
        message.chat.id,
        f"ivwith {report_label}",
        run_sales_report,
        bot,
        message.chat.id,
        report_type,
        report_label,
        sales_key,
        sales_display,
        weeks,
        build_customer_report,
        base_dir,
    )
    bot.send_message(message.chat.id, show_list())
    return True


def _sorted_counter_items(counter):
    def _key(item):
        label, count = item
        priority = STATUS_PRIORITY.index(label) if label in STATUS_PRIORITY else len(STATUS_PRIORITY)
        return (priority, -count, label)

    return sorted(counter.items(), key=_key)


def build_progress_report(base_dir, sales_key, sales_display, weeks):
    csv_path = _resolve_flow_summary_csv(base_dir)
    if not csv_path.is_file():
        raise FileNotFoundError(f"missing summary csv: {csv_path}")

    today = datetime.date.today()
    cut = today - datetime.timedelta(days=weeks)
    total_rows = 0
    status_counts = Counter()
    week_counts = Counter()
    watch_rows = []
    latest_rows = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get("현재영업자") or "").strip() != sales_key:
                continue
            current_date = _parse_iso_date(row.get("현재접수일"))
            if not current_date or current_date < cut:
                continue

            total_rows += 1
            status = _normalize_status(row)
            week_label = _normalize_week(row)
            status_counts[status] += 1
            week_counts[week_label] += 1

            due_date = _parse_iso_date(row.get("현재기표예정일"))
            alert = ""
            if status == "긴급관리":
                alert = "긴급관리"
            elif status == "기표예정" and due_date and due_date <= today:
                alert = f"기표예정+{(today - due_date).days}일"
            elif status == "진행보류":
                alert = "진행보류"
            if alert:
                watch_rows.append(
                    {
                        "date": current_date,
                        "name": _normalize_name(row),
                        "status": status,
                        "week": week_label,
                        "bank": _normalize_bank(row),
                        "loan": _normalize_loan(row.get("현재대출금액(만원)")),
                        "phone": _normalize_phone(row),
                        "alert": alert,
                    }
                )

            latest_rows.append(
                {
                    "date": current_date,
                    "name": _normalize_name(row),
                    "status": status,
                    "week": week_label,
                    "bank": _normalize_bank(row),
                    "loan": _normalize_loan(row.get("현재대출금액(만원)")),
                    "phone": _normalize_phone(row),
                    "note": _normalize_note(row),
                }
            )

    lines = [
        f"<b>📊 {escape(sales_display)} 현재 진행상태 리포트</b>",
        f"기준: 고객흐름_요약.csv / 최근 {weeks // 7}주 / 현재접수일 기준",
        f"전체: {total_rows}건",
    ]

    lines.append("")
    lines.append("<b>상태요약</b>")
    if status_counts:
        for label, count in _sorted_counter_items(status_counts):
            lines.append(f"- {escape(label)}: {count}건")
    else:
        lines.append("- 없음")

    lines.append("")
    lines.append("<b>지속관리 주차</b>")
    if week_counts:
        for label, count in sorted(week_counts.items(), key=lambda item: (-item[1], item[0]))[:8]:
            lines.append(f"- {escape(label)}: {count}건")
    else:
        lines.append("- 없음")

    lines.append("")
    lines.append("<b>주의목록</b>")
    if watch_rows:
        for item in sorted(
            watch_rows,
            key=lambda row: (0 if row["alert"] == "긴급관리" else 1, -row["date"].toordinal(), row["name"]),
        )[:10]:
            lines.append(
                "- "
                f"{item['date'].isoformat()[5:]} "
                f"{escape(item['name'])} "
                f"{escape(item['bank'])} "
                f"{escape(item['status'])} "
                f"{escape(item['week'])} "
                f"대{escape(item['loan'])} "
                f"{escape(item['phone'])} "
                f"⚠{escape(item['alert'])}"
            )
    else:
        lines.append("- 없음")

    lines.append("")
    lines.append("<b>최근접수 샘플</b>")
    if latest_rows:
        for item in sorted(latest_rows, key=lambda row: row["date"], reverse=True)[:10]:
            base = (
                "- "
                f"{item['date'].isoformat()[5:]} "
                f"{escape(item['name'])} "
                f"{escape(item['bank'])} "
                f"{escape(item['status'])} "
                f"{escape(item['week'])} "
                f"대{escape(item['loan'])} "
                f"{escape(item['phone'])}"
            )
            note = item["note"]
            if note:
                base += f"\n  메모: {escape(note[:120])}"
            lines.append(base)
    else:
        lines.append("- 없음")

    return "\n".join(lines)


def run_sales_report(bot, chat_id, report_type, report_label, sales_key, sales_display, weeks, build_customer_report, base_dir):
    bot.send_message(chat_id, f"⏳ {sales_display} {report_label} 최근 {weeks // 7}주 조회 중...")
    try:
        if report_type == "progress":
            report = build_progress_report(base_dir, sales_key, sales_display, weeks)
        else:
            report = build_customer_report(sales_key, sales_display, weeks)
        _send_report(bot, chat_id, report)
    except Exception as exc:
        bot.send_message(chat_id, f"❌ 리포트 생성 실패: {exc}")
