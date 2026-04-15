def handle_state_35(
    *,
    bot,
    message,
    text,
    state,
    briefing_classified,
    start_ai_briefing_step2,
    clear_pending_briefing,
    show_list,
):
    if text == "1":
        rows = briefing_classified.get("past_due", [])
        if not rows:
            bot.send_message(message.chat.id, "\u274c 날짜지남 고객이 없습니다.")
            return True
        start_ai_briefing_step2(message.chat.id, rows=rows)
        return True
    if text == "2":
        rows = briefing_classified.get("this_week", [])
        if not rows:
            bot.send_message(message.chat.id, "\u274c 이번주 고객이 없습니다.")
            return True
        start_ai_briefing_step2(message.chat.id, rows=rows)
        return True
    if text == "3":
        rows = briefing_classified.get("future", [])
        if not rows:
            bot.send_message(message.chat.id, "\u274c 예정 고객이 없습니다.")
            return True
        start_ai_briefing_step2(message.chat.id, rows=rows)
        return True
    if text == "4":
        start_ai_briefing_step2(message.chat.id)
        return True
    if text == "5":
        state["user_state"] = 36
        bot.send_message(
            message.chat.id,
            "\U0001f4cb 분석할 고객 정보를 붙여넣으세요.\n(위 브리핑에서 원하는 부분을 복사해서 붙여넣기)",
        )
        return True
    if text == "0":
        clear_pending_briefing()
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True
    bot.send_message(
        message.chat.id,
        "1. 날짜지남 / 2. 이번주 / 3. 예정 / 4. 전체 / 5. 선택분석\n0. 메뉴로 돌아가기",
    )
    return True


def handle_state_36(
    *,
    bot,
    message,
    text,
    state,
    start_ai_briefing_step2,
    clear_pending_briefing,
    show_list,
):
    if text == "0":
        clear_pending_briefing()
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True
    start_ai_briefing_step2(message.chat.id, raw_text=text)
    return True
