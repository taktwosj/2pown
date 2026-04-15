import os


def _resolved_menu34_base_dir(default_base_dir, menu34_base_dir):
    candidate = str(menu34_base_dir or "").strip()
    if not candidate:
        return default_base_dir

    required_paths = (
        os.path.join(candidate, "ivwith", "daily_sync.py"),
        os.path.join(candidate, "lockfile.py"),
        os.path.join(candidate, "runtime", "last_sync.json"),
        os.path.join(candidate, "config", "canonical_map.local.json"),
    )
    if all(os.path.exists(path) for path in required_paths):
        return candidate
    return default_base_dir


def handle_state_0(
    *,
    bot,
    message,
    text,
    state,
    ivwith_available,
    ivwith_menu,
    menu_script_map,
    show_list,
    start_background_task,
    base_dir,
    python_exe,
    resolve_runtime_path,
    send_long_message,
    format_script_search_message,
    format_sales_menu,
    resolve_script_path,
    display_script_name,
    format_ms_consent_unavailable_message,
    prompt_excel_customer_input,
    format_due_customer_menu,
    format_rt_watch_menu,
    start_ai_briefing_step1,
    send_claude_channel_redirect,
    run_wp_notice_post,
    menu34_base_dir="",
):
    if text in ("10", "34") and ivwith_available:
        ivwith_base_dir = _resolved_menu34_base_dir(base_dir, menu34_base_dir)
        ivwith_menu.start_menu_34(
            bot,
            message.chat.id,
            start_background_task,
            show_list,
            ivwith_base_dir,
        )
        return True

    if text in ("11", "35") and ivwith_available:
        state["user_state"] = 40
        ivwith_menu.start_menu_35(bot, message.chat.id, format_sales_menu)
        return True

    if text == "38" and ivwith_available:
        ivwith_base_dir = _resolved_menu34_base_dir(base_dir, menu34_base_dir)
        ivwith_menu.start_menu_38(
            bot,
            message.chat.id,
            start_background_task,
            show_list,
            ivwith_base_dir,
            python_exe,
            resolve_runtime_path,
            send_long_message,
            format_script_search_message,
        )
        return True

    if text == "71":
        bot.send_message(message.chat.id, "⏳ 최근 10일 공고문 확인 중...")
        start_background_task(message.chat.id, "공고문 포스팅", run_wp_notice_post, message.chat.id)
        return True

    if text == "81":
        state["user_state"] = 16
        bot.send_message(message.chat.id, format_rt_watch_menu())
        return True

    if text == "2":
        state["user_state"] = 18
        bot.send_message(
            message.chat.id,
            (
                "📝 [익시오 상담요약]\n"
                "익시오에서 공유한 통화 원문을 붙여넣어 주세요.\n"
                "Claude가 3개 말풍선(카톡접수용 / 내부 admin 접수용 / 엑셀 붙여넣기용)으로 정리합니다."
            ),
        )
        return True

    if text == "31":
        prompt_excel_customer_input(message.chat.id)
        return True

    if text in ("69", "33"):
        state["user_state"] = 23
        bot.send_message(message.chat.id, format_due_customer_menu(message.chat.id))
        return True

    if text in ("68", "32"):
        start_ai_briefing_step1(message.chat.id)
        return True

    if text == "80":
        send_claude_channel_redirect(message.chat.id)
        return True

    selected_file = menu_script_map.get(text)
    if not selected_file:
        bot.send_message(message.chat.id, show_list())
        return True

    target_path = resolve_script_path(selected_file)
    if not target_path:
        if text == "4":
            bot.send_message(message.chat.id, format_ms_consent_unavailable_message())
        else:
            bot.send_message(message.chat.id, format_script_search_message(selected_file))
        bot.send_message(message.chat.id, show_list())
        return True

    if text == "1":
        state["user_state"] = 1
        state["auto_script"] = target_path
        bot.send_message(
            message.chat.id,
            (
                f"📝 [{os.path.basename(target_path)}]\n"
                "카톡 고객 정보를 붙여넣어 주세요.\n"
                "입력 후 전체 라벨/값 확인 화면(1 진행 / 2 수정 / 3 엑셀입력 / 0 초기화)이 표시됩니다."
            ),
        )
        return True

    if text == "3":
        state["user_state"] = 6
        state["target_script"] = target_path
        bot.send_message(
            message.chat.id,
            (
                f"🆕 [{display_script_name(selected_file)}] admin접수 모드\n"
                "고객 정보를 붙여넣어 주세요.\n"
                "입력 후 전체 라벨/값 확인 화면이 나오며, 1 진행 / 2 수정 / 3 엑셀입력 / 0 초기화로 처리됩니다.\n"
                "예시:\n"
                "이름\n주민번호\n연락처\n주소\n보증금:1000\n대출금:1000\n접수:ms\n종류:대환\n직장인\nKT\n신용:회복\n기타사항:상세내용"
            ),
        )
        return True

    if text == "4":
        state["user_state"] = 30
        state["target_script"] = target_path
        bot.send_message(
            message.chat.id,
            (
                "📝 [MS신용조회동의]\n"
                "고객 정보를 입력하세요.\n"
                "이름 / 주민번호 / 연락처\n\n"
                "예시:\n"
                "홍길동\n900101-1234567\n010-1234-5678"
            ),
        )
        return True

    if text in {"6", "7"}:
        state["user_state"] = 3
        state["target_script"] = target_path
        label = "MS결과확인" if text == "6" else "키움결과확인"
        bot.send_message(message.chat.id, f"🔍 [{label}]\n조회할 '고객 이름'을 입력하세요.")
        return True

    if text == "5":
        state["user_state"] = 4
        state["target_script"] = target_path
        bot.send_message(
            message.chat.id,
            (
                f"🆕 [{display_script_name(selected_file)}] 신규접수 모드\n"
                "고객 정보를 붙여넣어 주세요.\n"
                "입력 후 전체 라벨/값 확인 화면이 나오며, 1 진행 / 2 수정 / 3 엑셀입력 / 0 초기화로 처리됩니다.\n"
                "예시:\n"
                "이름\n주민번호\n연락처\n주소\n접수:키움민간\n대출금:1000\n기타:회복중 프리랜서"
            ),
        )
        return True

    bot.send_message(message.chat.id, show_list())
    return True
