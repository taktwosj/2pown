def handle_state_18(*, message, text, start_ixio_summary):
    start_ixio_summary(message.chat.id, text)
    return True


def handle_state_19(
    *,
    bot,
    message,
    text,
    state,
    resolve_script_path,
    format_script_search_message,
    show_list,
    format_ixio_kakao_message,
    build_ixio_admin_payload,
    prepare_admin_flow,
    send_ixio_action_menu,
    start_excel_write_flow,
):
    choice = text.strip()
    if choice == "1":
        bot.send_message(message.chat.id, format_ixio_kakao_message(state["pending_ixio_data"] or {}))
        send_ixio_action_menu(message.chat.id)
        return True
    if choice == "2":
        admin_script = resolve_script_path("admin접수.py")
        if not admin_script:
            state["pending_ixio_data"] = {}
            state["pending_ixio_duplicates"] = []
            state["user_state"] = 0
            bot.send_message(message.chat.id, format_script_search_message("admin접수.py"))
            bot.send_message(message.chat.id, show_list())
            return True
        state["auto_script"] = admin_script
        admin_payload = build_ixio_admin_payload(state["pending_ixio_data"] or {})
        state["pending_ixio_data"] = {}
        state["pending_ixio_duplicates"] = []
        bot.send_message(
            message.chat.id,
            "ℹ️ admin접수 후 접수은행에 따라 MS/키움 후속접수까지 이어집니다.",
        )
        prepare_admin_flow(message.chat.id, admin_payload)
        return True
    if choice != "3":
        bot.send_message(message.chat.id, "1/2/3/0 중에서 입력해 주세요.")
        return True
    start_excel_write_flow(message.chat.id, state["pending_ixio_data"] or {}, resume="ixio")
    return True


def handle_state_20(
    *,
    bot,
    message,
    text,
    resume_after_excel,
    execute_excel_write_flow,
):
    choice = text.strip()
    if choice in {"2", "아니오", "아니요"}:
        resume_after_excel(message.chat.id, "ℹ️ 중복 가능성이 있어 엑셀 입력을 취소했습니다.")
        return True
    if choice != "1":
        bot.send_message(message.chat.id, "1(예) / 2(아니오) / 0(초기화면) 중에서 입력해 주세요.")
        return True
    execute_excel_write_flow(message.chat.id, skip_duplicate_check=True)
    return True


def handle_state_21(
    *,
    bot,
    message,
    text,
    build_excel_data_from_text,
    start_excel_write_flow,
):
    ok, excel_data = build_excel_data_from_text(text)
    if not ok:
        bot.send_message(
            message.chat.id,
            f"❌ 엑셀 입력 준비 실패\n{excel_data}\n\n양식에 맞춰 다시 붙여넣어 주세요. (카톡 고객정보 / admin 라벨형 / 엑셀 한 줄)"
        )
        return True
    start_excel_write_flow(message.chat.id, excel_data, resume="list")
    return True


def handle_state_22(
    *,
    bot,
    message,
    text,
    state,
    show_list,
    execute_excel_write_flow,
    resume_after_excel,
):
    choice = text.strip()
    if choice in {"0", "00", "취소"}:
        state["pending_excel_data"] = {}
        state["pending_excel_resume"] = ""
        state["user_state"] = 0
        bot.send_message(message.chat.id, show_list())
        return True
    if choice in {"1", "예"}:
        execute_excel_write_flow(message.chat.id)
        return True
    if choice in {"2", "수정"}:
        if state["pending_excel_resume"] == "list":
            state["pending_excel_data"] = {}
            state["pending_excel_resume"] = ""
            state["user_state"] = 21
            bot.send_message(
                message.chat.id,
                "수정할 내용을 다시 붙여넣어 주세요.\n지원 형식: 카톡 고객정보 / admin 라벨형 / 엑셀 한 줄\n0. 초기화면"
            )
            return True
        resume_after_excel(message.chat.id)
        return True
    bot.send_message(message.chat.id, "1(예) / 2(수정) / 0(초기화면) 중에서 입력해 주세요.")
    return True
