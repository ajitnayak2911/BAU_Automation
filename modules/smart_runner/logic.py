from concurrent.futures import ThreadPoolExecutor
import asyncio

from modules.badge_caps.logic import run_badge_caps_for_url
from modules.dummy_links.logic import run_dummy_links_single
from modules.link_audit.logic import analyze_links
from modules.form_tester.logic import run_single_url
from modules.seo_meta.logic import run_single_url as run_seo_meta


def run_selected_usecases_parallel(url, selected_usecases):

    results = {}

    def run_badge():
        return run_badge_caps_for_url(url)

    def run_dummy():
        return run_dummy_links_single(url)

    def run_audit():
        audit_result, error = analyze_links(url)
        return audit_result if not error else error

    def run_form():
        return asyncio.run(run_single_url(url))

    task_map = {
        "Badge Caps": run_badge,
        "Dummy Links": run_dummy,
        "Link Audit": run_audit,
        "Form Tester": run_form,
        "SEO Meta": lambda: run_seo_meta(url),
    }

    with ThreadPoolExecutor(max_workers=len(selected_usecases)) as executor:
        future_map = {
            name: executor.submit(task_map[name])
            for name in selected_usecases
        }

        for name, future in future_map.items():
            results[name] = future.result()

    return results

