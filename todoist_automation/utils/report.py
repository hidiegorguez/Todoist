def build_daily_report(today, messages_dict, fantasy_msg, permanenttasks_msg, runtime_seconds):
    """Assemble the Daily Todoist email body from the per-block message lists."""
    body = f'Todoist Automation for {today.strftime("%Y-%m-%d")}\n'
    count = 1
    for title, msgs in messages_dict.items():
        if msgs != []:
            body += "\n" + f"{count}. " + title + "\n"
            for msg in msgs:
                body += "  " + msg + "\n"
            count += 1
    if fantasy_msg != []:
        body += "\n" + f"{count}. " + fantasy_msg[0] + "\n"
    if permanenttasks_msg != []:
        if permanenttasks_msg[0][:2] != "- ":
            body += "\n" + f"{count}. " + permanenttasks_msg[0] + "\n"
        else:
            body += "\n" + f"{count}. Permanent task to uncomplete: \n"
            for msg in permanenttasks_msg:
                body += "  " + msg + "\n"
    if body == f'Todoist Automation for {today.strftime("%Y-%m-%d")}\n':
        body += '\nNo changes\n'
    body += "\n" + f'Runtime: {round(runtime_seconds, 3)} seconds'
    return body
