from config_loader import load_config
from providers.claude import ClaudeProvider
from providers.opencode import OpenCodeProvider
from providers.ollama import OllamaProvider
from providers.zai import ZaiProvider
from calculators import calculate_budget, calculate_burst
from history import History
from ui import render


def main():
    config = load_config()

    providers = []

    # Claude
    providers.append(ClaudeProvider().fetch())

    # OpenCode
    oc_config = config.get("opencode_go", {})
    if "billing_cycle_start" in oc_config:
        oc = OpenCodeProvider(oc_config["billing_cycle_start"]).fetch()
        history = History()
        trailing = history.get_trailing_avg(oc.name)
        if oc.remaining_quota is not None:
            history.save_snapshot(oc.name, oc.remaining_quota)
        providers.append(calculate_budget(oc, trailing))

    # Ollama
    ol_config = config.get("ollama_cloud", {})
    if "cookie" in ol_config:
        ol = OllamaProvider(ol_config["cookie"]).fetch()
        providers.append(calculate_burst(ol))

    # Zai
    zai_config = config.get("zai_glm", {})
    if zai_config.get("api_key") or True:  # always allow manual input
        st = ZaiProvider(zai_config.get("api_key", "")).fetch()
        if st.remaining_quota is not None:
            history = History()
            trailing = history.get_trailing_avg(st.name)
            history.save_snapshot(st.name, st.remaining_quota)
            providers.append(calculate_budget(st, trailing))
        else:
            providers.append(calculate_burst(st))

    render(providers)


if __name__ == "__main__":
    main()
