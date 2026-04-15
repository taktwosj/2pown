def handle_state_16(
    *,
    bot,
    message,
    text,
    state,
    format_rt_mode_menu,
    show_list,
):
    choice = text.strip()
    if choice in {"0", "00", "취소"}:
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True
    if choice == "1":
        state["pending_rt_months"] = 24
        state["pending_rt_print_history"] = True
        state["user_state"] = 17
        bot.send_message(
            message.chat.id,
            format_rt_mode_menu(state["pending_rt_months"], state["pending_rt_print_history"]),
        )
        return True
    if choice == "2":
        state["pending_rt_months"] = 12
        state["pending_rt_print_history"] = True
        state["user_state"] = 17
        bot.send_message(
            message.chat.id,
            format_rt_mode_menu(state["pending_rt_months"], state["pending_rt_print_history"]),
        )
        return True
    if choice == "3":
        state["pending_rt_months"] = 2
        state["pending_rt_print_history"] = False
        state["user_state"] = 17
        bot.send_message(
            message.chat.id,
            format_rt_mode_menu(state["pending_rt_months"], state["pending_rt_print_history"]),
        )
        return True
    if choice == "4":
        state["pending_rt_months"] = 1
        state["pending_rt_print_history"] = False
        state["user_state"] = 17
        bot.send_message(
            message.chat.id,
            format_rt_mode_menu(state["pending_rt_months"], state["pending_rt_print_history"]),
        )
        return True
    if choice.isdigit():
        state["pending_rt_months"] = max(1, min(36, int(choice)))
        state["pending_rt_print_history"] = False
        state["user_state"] = 17
        bot.send_message(
            message.chat.id,
            format_rt_mode_menu(state["pending_rt_months"], state["pending_rt_print_history"]),
        )
        return True
    bot.send_message(message.chat.id, "1/2/3/4 또는 조회개월(숫자), 0(초기화면)을 입력해 주세요.")
    return True


def handle_state_17(
    *,
    bot,
    message,
    text,
    state,
    start_background_task,
    run_rt_watch_background,
    show_list,
):
    choice = text.strip()
    if choice in {"0", "00", "취소"}:
        state["pending_rt_months"] = 12
        state["pending_rt_print_history"] = False
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True
    deal_filter = {"1": "all", "2": "trade", "3": "rent"}.get(choice)
    if not deal_filter:
        bot.send_message(message.chat.id, "1(전체) / 2(매매) / 3(전월세) / 0(초기화면) 중에서 입력해 주세요.")
        return True
    months = state["pending_rt_months"]
    print_history = state["pending_rt_print_history"]
    state["pending_rt_months"] = 12
    state["pending_rt_print_history"] = False
    state["user_state"] = 0
    start_background_task(
        message.chat.id,
        "빌라 실거래 조회",
        run_rt_watch_background,
        message.chat.id,
        months,
        print_history,
        deal_filter,
    )
    bot.send_message(message.chat.id, show_list())
    return True
