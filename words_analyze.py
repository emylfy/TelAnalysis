import json
import re
import time

import jmespath
import phonenumbers
from pywebio import output, pin, session
from validate_email import validate_email
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import nltk_analyse
from utils import read_conf

# Render cap: how many messages per user are rendered into the page DOM.
# Above this, the full set is offered as a CSV download instead.
_PER_USER_MSG_CAP = 500

action_map = {
    "invite_members": "Invite Member",
    "remove_members": "Kicked Members",
    "join_group_by_link": "Joined by Link",
    "pin_message": "Pinned Message",
}

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    try:
        score = analyzer.polarity_scores(str(text))
        return float(score["compound"])
    except Exception:
        return 0.0


def extract_emails_and_phone_numbers(text):
    emails_list = []
    for email in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        if validate_email(email, verify=False):
            emails_list.append(email)
    phones_list = []
    for phones in re.findall(
        r"\+?[0-9]{1,3}?[-. (]?[0-9]{1,4}[-. )]?[0-9]{1,4}[-. ]?[0-9]{1,9}", text
    ):
        try:
            parsed = phonenumbers.parse(phones, None)
            if phonenumbers.is_valid_number(parsed):
                phones_list.append(phones)
        except Exception:
            pass
    return emails_list, phones_list


def extract_text_from_message(message):
    texts = set()
    if isinstance(message, dict):
        if "text" in message:
            t = message["text"]
            if isinstance(t, str) and t.strip():
                texts.add(t)
            elif isinstance(t, list):
                for item in t:
                    if isinstance(item, str):
                        texts.add(item)
        if "caption" in message:
            c = message["caption"]
            if isinstance(c, str) and c.strip():
                texts.add(c)
        entities = jmespath.search("text_entities[*].text", message)
        if entities:
            for e in entities:
                texts.add(e)
        if "forwarded_from" in message:
            texts.update(extract_text_from_message(message["forwarded_from"]))
        if "reply_to_message" in message:
            texts.update(extract_text_from_message(message["reply_to_message"]))
        for value in message.values():
            if isinstance(value, (list, dict)):
                texts.update(extract_text_from_message(value))
    elif isinstance(message, list):
        for item in message:
            texts.update(extract_text_from_message(item))
    return texts


def words(path):
    """Run word + sentiment analysis on a single chat JSON.
    Renders into the current pywebio session."""
    t0 = time.time()

    output.put_button(
        "Scroll Down",
        onclick=lambda: session.run_js(
            "window.scrollTo(0, document.body.scrollHeight)"
        ),
    )
    output.put_html("<h1><center>Analyse of Telegram Chat<center></h1><br>")
    pin.put_input("ID")
    output.put_button(
        "Search ID",
        onclick=lambda: session.run_js(f"window.find({pin.pin.ID}, true)"),
        color="warning",
    )

    filename = path.split(".")[0].split("/")[1]
    output.put_markdown(f"**[1/5]** Loading `{filename}.json`…")
    print(f"[words] loading asset/{filename}.json", flush=True)

    with open(
        f"asset/{filename}.json", "r", encoding="utf-8", errors="replace"
    ) as datas:
        data = json.load(datas)

    sf = jmespath.search("messages[*]", data) or []
    group_name = jmespath.search("name", data)
    print(f"[words] {len(sf)} messages, group_name={group_name!r}", flush=True)

    # Session-local state (no module globals)
    emails = []
    phoness = []
    all_tokens = []
    users = {}

    def process_message(message):
        user = jmespath.search("from_id", message)
        if not user:
            user = jmespath.search("actor_id", message)
            if user is None:
                # service msg without an actor — nothing to attribute
                return
            user = user.replace(" ", "")
            users.setdefault(user, [])
            action = jmespath.search("action", message)
            if action:
                tex = jmespath.search("text", message) or ""
                action_text = action_map.get(action, action)
                if action in ("invite_members", "remove_members"):
                    members = jmespath.search("members", message) or []
                    members_str = ",".join(str(x) for x in members if x)
                    users[user].append((f"{action_text} - {members_str}", 0.0))
                else:
                    users[user].append((f"{action_text} {tex}", 0.0))
                return

        user = user.replace(" ", "")
        users.setdefault(user, [])
        for clean_text in extract_text_from_message(message):
            if not clean_text:
                continue
            sentiment_score = analyze_sentiment(clean_text)
            users[user].append((clean_text, sentiment_score))
            ex_emails, ex_phones = extract_emails_and_phone_numbers(clean_text)
            emails.extend(ex_emails)
            phoness.extend(ex_phones)

    total = len(sf)
    output.put_markdown(
        f"**[2/5]** Extracting text + sentiment from **{total}** messages…"
    )
    output.put_processbar("words_extract", init=0)
    step = max(1, total // 200)
    for i, msg in enumerate(sf):
        try:
            process_message(msg)
        except Exception as e:
            print(f"Error processing message: {e}")
        if i % step == 0 or i == total - 1:
            output.set_processbar("words_extract", (i + 1) / max(total, 1))

    print(
        f"[words] processed {total} messages in {time.time() - t0:.1f}s, "
        f"{len(users)} users, {len(emails)} emails, {len(phoness)} phones",
        flush=True,
    )

    # from_id -> from-name index (single pass, was O(n²))
    user_name_index = {}
    for m in sf:
        fid = jmespath.search("from_id", m)
        if fid and fid not in user_name_index:
            user_name_index[fid] = jmespath.search("from", m)

    n_users = len(users)
    output.put_markdown(
        f"**[3/5]** Per-user word + sentiment analysis ({n_users} users)…"
    )
    output.put_processbar("words_users", init=0)
    ustep = max(1, n_users // 100)

    most_com = read_conf("most_com")

    for u_idx, (user, da) in enumerate(users.items()):
        if u_idx % ustep == 0 or u_idx == n_users - 1:
            output.set_processbar("words_users", (u_idx + 1) / max(n_users, 1))

        user_from = user_name_index.get(user, "")
        user_display = f"{user_from} - {user}" if user_from else user

        user_sentiment_scores = [float(x[1]) for x in da if isinstance(x[1], float)]
        avg_user_sent = (
            sum(user_sentiment_scores) / len(user_sentiment_scores)
            if user_sentiment_scores
            else 0
        )

        try:
            genuy, tokens = nltk_analyse.analyse(da, most_com)
            gemy = [[x, y] for x, y in genuy]
            all_tokens.extend(tokens)

            if not da and not gemy:
                continue

            msgs_full = [[x[0], x[1]] for x in da]
            n_msgs = len(msgs_full)
            cap = _PER_USER_MSG_CAP
            truncated = n_msgs > cap
            msgs_show = msgs_full[:cap]

            user_csv_bytes = None
            if truncated:
                safe_user = re.sub(r"[^\w\-]+", "_", str(user))
                csv_path = f"asset/messages_{filename}_{safe_user}.csv"
                with open(csv_path, "w", encoding="utf-8") as fh:
                    fh.write("text,sentiment\n")
                    for t, s in msgs_full:
                        t_safe = (
                            '"'
                            + str(t)
                            .replace('"', '""')
                            .replace("\n", " ")
                            .replace("\r", " ")
                            + '"'
                        )
                        fh.write(f"{t_safe},{s}\n")
                with open(csv_path, "rb") as fh:
                    user_csv_bytes = fh.read()

            contents = [
                f"Messages of {user_display}",
                output.put_text(
                    f"Average Sentiment for {user_display}: {avg_user_sent:.2f}"
                ),
            ]
            if truncated:
                contents.append(
                    output.put_text(
                        f"Showing {cap:,} of {n_msgs:,} messages — full list in CSV download below"
                    )
                )
            contents.append(
                output.put_table(msgs_show, header=["Messages", "Sentiment Score"])
            )
            if truncated and user_csv_bytes is not None:
                contents.append(
                    output.put_file(
                        f"messages_{user}.csv",
                        label=f"Download all {n_msgs:,} messages (CSV)",
                        content=user_csv_bytes,
                    )
                )
            contents.append(output.put_table(gemy, header=["word", "count"]))

            output.put_collapse(user_display, contents, open=False)
        except Exception as ex:
            print(f"[{user}] error: {ex}")

    output.set_processbar("words_users", 1.0)
    print(f"[words] per-user analysis done in {time.time() - t0:.1f}s", flush=True)

    output.put_markdown(f"**[4/5]** Aggregating top words across chat…")
    try:
        all_tokens, _top_data = nltk_analyse.analyse_all(all_tokens, most_com)
    except Exception as e:
        print(f"Error in analyse_all: {e}")
        all_tokens = []

    if all_tokens:
        all_chat = [[i[0], i[1]] for i in all_tokens]
        output.put_collapse(
            f"TOP words of {group_name}",
            [output.put_table(all_chat, header=["word"])],
            open=False,
        )
        all_sentiment_scores = [analyze_sentiment(t[0]) for t in all_tokens]
        avg_chat_sent = (
            sum(all_sentiment_scores) / len(all_sentiment_scores)
            if all_sentiment_scores
            else 0
        )
        output.put_text(f"Average Sentiment for {group_name}: {avg_chat_sent:.2f}")
    else:
        output.put_text(
            f"No tokens found for {group_name}. Sentiment analysis is unavailable."
        )

    output.put_markdown(f"**[5/5]** Rendering emails & phone numbers…")
    emaills = [[e] for e in set(emails)]
    phonness = [[p] for p in set(phoness)]
    output.put_collapse(
        "Finded Emails and Numbers",
        [
            output.put_table(emaills, header=["Emails:"]),
            output.put_table(phonness, header=["Numbers:"]),
        ],
        open=False,
    )

    elapsed = time.time() - t0
    output.put_markdown(
        f"**Done** in {elapsed:.1f}s — {n_users} users, "
        f"{len(set(emails))} unique emails, {len(set(phoness))} unique phones"
    )
    print(f"[words] complete in {elapsed:.1f}s", flush=True)

    output.put_button(
        "Scroll Up",
        onclick=lambda: session.run_js(
            "window.scrollTo(document.body.scrollHeight, 0)"
        ),
    )
