# Telanalysis by Eduard Isaev @e_isaevsan

from pywebio import start_server, input, config
from pywebio.output import (
    put_html,
    put_text,
    put_image,
    put_button,
    put_table,
    put_collapse,
    put_code,
    clear,
    put_file,
    Output,
    toast,
    put_processbar,
    set_processbar,
    put_markdown,
)
from pywebio.input import file_upload as file
from pywebio.session import run_js
from pywebio.input import select, slider
import json, re, jmespath, string, collections, time
from utils import (
    remove_chars_from_text,
    remove_emojis,
    clear_user,
    clear_console,
    read_conf,
    write_conf,
    open_url,
    is_full_export,
    build_chat_options,
    find_chat_by_id,
    write_chat_as_single,
)
import nltk_analyse, channel_analyse, words_analyze
import networkx as nx
import matplotlib.pyplot as plt
import sys
import matplotlib

matplotlib.use("Agg")

global select_type_stem


## config pywebio
config(
    theme="dark",
    title="TelAnalysis",
    description="Analysing Telegram CHATS-CHANNELS-GROUPS",
)


def generator(filename):
    import collections  # Импортируем здесь, если используется в функции
    import networkx as nx
    import matplotlib.pyplot as plt

    tables = []
    clear_console()
    filename = filename.split(".")[0]
    filename = filename.split("/")[1]
    dates_list = []
    names = []

    open(f"asset/edges_{filename}.csv", "w", encoding="utf-8").write(
        "source,target,label"
    )

    import time as _time

    _t0 = _time.time()
    put_markdown(f"**[1/4]** Loading `{filename}.json`…")
    print(f"[gen] loading asset/{filename}.json", flush=True)

    with open(f"asset/{filename}.json", "r", encoding="utf-8") as f:
        jsondata = json.load(f)
        group_name = jmespath.search("name", jsondata)
        put_html(f"<center><h1>{group_name}</h1><center>")
        sf = jmespath.search("messages[*]", jsondata) or []
        total = len(sf)
        put_markdown(f"**[2/4]** Building edges from **{total}** messages…")
        print(f"[gen] {total} messages, building id index", flush=True)

        # O(1) reply lookup
        id_index = {}
        for m in sf:
            mid = m.get("id") if isinstance(m, dict) else None
            if mid is not None:
                id_index[mid] = m

        put_processbar("gen", init=0)
        edges_buf = []
        step = max(1, total // 200)

        for i, message in enumerate(sf):
            if i % step == 0 or i == total - 1:
                set_processbar("gen", (i + 1) / max(total, 1))

            fromm = jmespath.search("from", message)
            if fromm is None:
                continue
            from_id = jmespath.search("from_id", message)
            date = jmespath.search("date", message)
            dates_list.append(date)

            if from_id in ["source", "target", None]:
                continue

            name_id = f"{fromm}, {from_id}"
            names.append(name_id)

            text_message = jmespath.search("text", message)
            if isinstance(text_message, list):
                for textt in message:
                    try:
                        if isinstance(textt, dict) and "text" in textt:
                            test = textt["text"]
                        elif isinstance(textt, str):
                            test = textt
                        else:
                            continue

                        test = test.replace("\\n", "").replace("\n", "").strip()
                        try:
                            message_clean = remove_emojis(test)
                        except:
                            message_clean = test
                    except Exception as ex:
                        print(f"Error: {ex}")
                        continue

            else:
                try:
                    message_clean = remove_emojis(text_message)
                except:
                    message_clean = text_message

            if not message_clean:
                continue

            reply_to_message_id = jmespath.search("reply_to_message_id", message)
            if reply_to_message_id:
                reply_message = id_index.get(reply_to_message_id)
                if reply_message is not None:
                    reply_to = jmespath.search("from", reply_message)
                    reply_to_id = jmespath.search("from_id", reply_message)
                    reply_name_id = f"{reply_to}, {reply_to_id}"
                    names.append(reply_name_id)
                    edges_buf.append(f"\n{from_id},{reply_to_id},{fromm}-{reply_to}")
            else:
                edges_buf.append(f"\n{from_id},{from_id},{fromm}")

        with open(f"asset/edges_{filename}.csv", "a", encoding="utf-8") as ef:
            ef.write("".join(edges_buf))

        set_processbar("gen", 1.0)
        print(
            f"[gen] edges built in {_time.time() - _t0:.1f}s, "
            f"{len(edges_buf)} edges, {len(set(names))} unique participants",
            flush=True,
        )

        put_markdown(f"**[3/4]** Building nodes…")
        # Создаем nodes.csv
        open(f"asset/nodes_{filename}.csv", "w", encoding="utf-8").write(
            "id,label,weight"
        )
        with open(f"asset/nodes_{filename}.csv", "a", encoding="utf-8") as odin:
            c = collections.Counter(names)
            users_table = []
            for i in c:
                id_stroka = i.split(",")[1]
                if id_stroka in ["id", "label", "weight", "None"]:
                    continue

                name_stroka = i.split(",")[0]
                weight = c[i]
                users_table.append([id_stroka.replace("user", ""), name_stroka, weight])
                odin.write(f"\n{id_stroka},{name_stroka},{weight}")

        print(f"[gen] {len(users_table)} nodes written", flush=True)
        # Render cap on users table — keeps DOM small on huge groups
        users_cap = 500
        users_table_sorted = sorted(users_table, key=lambda r: -int(r[2]))
        if len(users_table_sorted) > users_cap:
            put_text(
                f"Showing top {users_cap} of {len(users_table_sorted)} participants by message count — full list in nodes CSV below"
            )
            put_table(
                users_table_sorted[:users_cap],
                header=["USER ID", "USERNAME", "COUNT"],
            )
        else:
            put_table(users_table_sorted, header=["USER ID", "USERNAME", "COUNT"])

    # Графовые лимиты для отрисовки: matplotlib не справляется с тысячами узлов
    GRAPH_DRAW_MAX_NODES = 500
    GRAPH_LABEL_MAX_NODES = 200

    put_markdown(f"**[4/4]** Drawing graph…")
    # Визуализация графа
    try:
        G = nx.DiGraph()  # Создание графа

        # Чтение узлов
        with open(f"asset/nodes_{filename}.csv", "r", encoding="utf-8") as nodes:
            for node in nodes:
                node = node.strip()
                if node == "" or node.startswith("id,label,weight"):
                    continue  # Пропускаем заголовок и пустые строки

                parts = node.split(",")
                if len(parts) != 3:
                    print(f"Skipping malformed node line: {node}")
                    continue

                ids, label, weight = parts
                try:
                    weight = float(weight)
                    if weight < 0:
                        weight = 1
                except ValueError:
                    print(
                        f"Invalid weight value: {weight} for node {label}. Skipping..."
                    )
                    continue

                G.add_node(label, weight=weight)

        # Чтение рёбер
        with open(f"asset/edges_{filename}.csv", "r") as edges:
            for edge in edges:
                if "source,target,label" in edge or "None" in edge:
                    continue
                source, target, label = edge.strip().split(",")
                G.add_edge(source, target, weight=1.3)

        n_nodes = len(G.nodes)
        n_edges = len(G.edges)
        print(f"[gen] graph: {n_nodes} nodes, {n_edges} edges", flush=True)

        if n_nodes == 0:
            put_markdown("**Graph skipped** — no nodes")
        elif n_nodes > GRAPH_DRAW_MAX_NODES:
            print(
                f"[gen] skipping graph render: {n_nodes} > {GRAPH_DRAW_MAX_NODES} cap",
                flush=True,
            )
            put_markdown(
                f"**Graph too large to draw** — {n_nodes} nodes exceeds cap of "
                f"{GRAPH_DRAW_MAX_NODES}. Use the **Edges**/**Nodes** CSVs below in "
                f"[Gephi](https://gephi.org) for interactive viz."
            )
            put_markdown(
                f"**Done** in {_time.time() - _t0:.1f}s — {n_nodes} nodes, {n_edges} edges"
            )
        else:
            sizes = []
            colors = []
            labels = {}
            show_labels = n_nodes <= GRAPH_LABEL_MAX_NODES

            for n in G.nodes:
                weight = G.nodes[n].get("weight", 1)
                if isinstance(weight, (int, float)) and weight >= 0:
                    min_size = 50
                    scale_factor = 10
                    sizes.append(max(min_size, weight * scale_factor))
                    colors.append(weight)
                    if show_labels:
                        labels[n] = f"{n} - {weight}"
                else:
                    print(
                        f"Invalid weight for node {n}: {weight} (type: {type(weight)})"
                    )

            pos = nx.circular_layout(G)
            nx.draw(
                G,
                pos,
                with_labels=show_labels,
                labels=labels if show_labels else None,
                font_weight="bold",
                node_size=sizes if sizes else 300,
                node_color=colors if colors else "blue",
                cmap=plt.cm.Blues,
            )
            plt.savefig(f"asset/{filename}.png", bbox_inches="tight")
            plt.close()
            note = (
                ""
                if show_labels
                else f" (labels hidden — >{GRAPH_LABEL_MAX_NODES} nodes)"
            )
            print(
                f"[gen] graph drawn: {n_nodes} nodes, {n_edges} edges, "
                f"total {_time.time() - _t0:.1f}s{note}",
                flush=True,
            )
            put_markdown(
                f"**Done** in {_time.time() - _t0:.1f}s — {n_nodes} nodes, {n_edges} edges{note}"
            )
    except Exception as ex:
        print(f"Error generating graph: {ex}")
        put_markdown(f"**Graph error:** `{ex}`")

    # Вывод даты первого и последнего сообщения
    firstmes = dates_list[0].replace("T", " ")
    lastmes = dates_list[-1].replace("T", " ")
    put_table([[firstmes]], header=["First Message"])
    put_table([[lastmes]], header=["Last Message"])

    # Отправка файлов
    try:
        nodes_content = open(f"asset/nodes_{filename}.csv", "rb").read()
        put_file(f"nodes_{filename}.csv", label="Nodes", content=nodes_content)
    except Exception as ex:
        put_text(f"Error: {ex}")

    try:
        edges_content = open(f"asset/edges_{filename}.csv", "rb").read()
        put_file(f"edges_{filename}.csv", label="Edges", content=edges_content)
    except Exception as ex:
        put_text(f"Error: {ex}")

    try:
        graph_content = open(f"asset/{filename}.png", "rb").read()
        put_file(f"{filename}.png", label="Graph", content=graph_content)
    except Exception as ex:
        put_text(f"Error: {ex}")

    put_button("clear", onclick=lambda: run_js("window.location.reload()"))
    put_button(
        "Scroll Up",
        onclick=lambda: run_js("window.scrollTo(document.body.scrollHeight, 0)"),
    )


def _upload_and_resolve_chat_path():
    """Upload a JSON, auto-detect single vs full export, return path 'asset/<safe>.json'.

    For full exports, prompts the user to pick one chat from a dropdown and writes
    that chat in single-export shape so the rest of the pipeline works unchanged.
    """
    import os

    os.makedirs("asset", exist_ok=True)
    f = file("Select a file:", accept=".json")
    raw_path = "asset/" + f["filename"]
    with open(raw_path, "wb") as fh:
        fh.write(f["content"])

    with open(raw_path, "r", encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)

    if not is_full_export(data):
        return raw_path

    options = build_chat_options(data)
    if not options:
        toast("No chats found in archive.", color="error", duration=4)
        raise RuntimeError("Empty chats.list in full export")

    chat_id = select("Pick a chat to analyse:", options=options)
    chat = find_chat_by_id(data, chat_id)
    if chat is None:
        raise RuntimeError(f"Chat {chat_id} not found")
    return write_chat_as_single(chat, asset_dir="asset")


def start_gen():
    clear_console()
    clear()
    put_button(
        "Scroll Down",
        onclick=lambda: run_js("window.scrollTo(0, document.body.scrollHeight)"),
    )
    put_button(
        "Return", onclick=lambda: run_js("window.location.reload()"), color="danger"
    )
    put_html("<h1><center>Graph of Telegram Chat<center></h1><br>")
    path = _upload_and_resolve_chat_path()
    print(path)
    generator(path)


def start_two():
    clear_console()
    clear()
    put_button(
        "Scroll Down",
        onclick=lambda: run_js("window.scrollTo(0, document.body.scrollHeight)"),
    )
    put_button(
        "Return", onclick=lambda: run_js("window.location.reload()"), color="danger"
    )
    put_html("<h1><center>Analyse of Telegram Chat<center></h1><br>")
    path = _upload_and_resolve_chat_path()
    words_analyze.words(path)


def start_three():
    clear_console()
    clear()
    put_button(
        "Scroll Down",
        onclick=lambda: run_js("window.scrollTo(0, document.body.scrollHeight)"),
    )
    put_html("<h1><center>Analyse of Telegram Channel<center></h1><br>")
    put_button(
        "Return", onclick=lambda: run_js("window.location.reload()"), color="danger"
    )
    path = _upload_and_resolve_chat_path()
    channel_analyse.channel(path)


def config():
    while True:
        clear_console()
        try:
            clear()
            put_button(
                "Close",
                onclick=lambda: run_js("window.location.reload()"),
                color="danger",
            )
            put_html("<h1><center>Configuration<center></h1>")
            put_text(f"select_type_stem: {read_conf('select_type_stem')}")
            put_text(f"most_common: {read_conf('most_com')}")
            put_text(f"most_common_channel: {read_conf('most_com_channel')}")
            select_type_stem = select("Stemming mode:", ["Off", "On"], multiple=False)
            most_com = read_conf("most_com")
            most_com_channel = read_conf("most_com_channel")
            write_conf(
                {
                    "select_type_stem": select_type_stem,
                    "most_com": most_com,
                    "most_com_channel": most_com_channel,
                }
            )
            toast("Config saved.")
        except Exception as ex:
            error = f"Error: {ex}"
            toast(error)
        try:
            clear()
            put_button(
                "Close",
                onclick=lambda: run_js("window.location.reload()"),
                color="danger",
            )
            put_html("<h1><center>Configuration<center></h1>")
            put_text(f"select_type_stem: {read_conf('select_type_stem')}")
            put_text(f"most_common: {read_conf('most_com')}")
            put_text(f"most_common_channel: {read_conf('most_com_channel')}")
            most_com = slider("Most Common words [USER]:")
            most_com_channel = read_conf("most_com_channel")
            write_conf(
                {
                    "select_type_stem": select_type_stem,
                    "most_com": most_com,
                    "most_com_channel": most_com_channel,
                }
            )
            toast("Config saved.")
        except Exception as ex:
            error = f"Error: {ex}"
            toast(error)
        try:
            clear()
            put_button(
                "Close",
                onclick=lambda: run_js("window.location.reload()"),
                color="danger",
            )
            put_html("<h1><center>Configuration<center></h1>")
            put_text(f"select_type_stem: {read_conf('select_type_stem')}")
            put_text(f"most_common: {read_conf('most_com')}")
            put_text(f"most_common_channel: {read_conf('most_com_channel')}")
            most_com_channel = slider("Most Common words [Channel]:")
            write_conf(
                {
                    "select_type_stem": select_type_stem,
                    "most_com": most_com,
                    "most_com_channel": most_com_channel,
                }
            )
            toast("Config saved.")
        except Exception as ex:
            error = f"Error: {ex}"
            toast(error)


def default():
    clear()
    clear_console()
    put_button("Config", onclick=config, color="warning")
    put_html("<h1><center>Welcome to TelAnalysis<center></h1>")
    put_html("<h3>Select a module:</h3>")
    put_button("Generating Graphs", onclick=start_gen)
    put_button("Analysing Chat", onclick=start_two)
    put_button("Analysing Channel", onclick=start_three)


def starting():
    clear_console()
    try:
        if not os.path.exists("config.json"):
            write_conf(
                {"select_type_stem": "Off", "most_com": 30, "most_com_channel": 100}
            )
        else:
            select_type_stem = read_conf("select_type_stem")
            most_com = read_conf("most_com")
            most_com_channel = read_conf("most_com_channel")
    except:
        write_conf({"select_type_stem": "Off", "most_com": 30, "most_com_channel": 100})
        pass
    while True:
        import nltk

        nltk.download("stopwords")
        nltk.download("punkt")
        nltk.download("punkt_tab")

        clear_console()
        try:
            import os

            if not os.path.exists("asset"):
                os.makedirs("asset")
            open_url()
            start_server(
                default, host="127.0.0.1", port=9993, debug=True, background="gray"
            )
        except KeyboardInterrupt:
            break
            exit()
        except Exception as ex:
            print(ex)
            break
    exit(1)


if __name__ == "__main__":
    starting()
