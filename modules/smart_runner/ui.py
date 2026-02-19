import streamlit as st
import pandas as pd
import concurrent.futures

from .logic import run_selected_usecases_parallel


def run():

    st.title("🚀 Smart Multi-UseCase Runner (Parallel Mode)")

    url = st.text_input("Enter URL")

    selected = st.multiselect(
        "Select Use Cases",
        [
            "Badge Caps",
            "Dummy Links",
            "Link Audit",
            "Form Tester",
            "SEO Meta"
        ]
    )

    if st.button("Run Selected Use Cases"):

        if not url.strip():
            st.warning("Please enter a URL")
            return

        if not selected:
            st.warning("Select at least one module")
            return

        results = {}
        total_modules = len(selected)
        completed = 0

        # ✅ Create overall progress bar
        overall_progress = st.progress(0)

        # ✅ Per-module progress + status
        progress_bars = {}
        module_status = {}

        for module in selected:
            module_status[module] = st.empty()
            module_status[module].info(f"{module} ⏳ Running...")
            progress_bars[module] = st.progress(0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=total_modules) as executor:

            future_map = {
                module: executor.submit(
                    run_selected_usecases_parallel,
                    url.strip(),
                    [module]
                )
                for module in selected
            }

            for future in concurrent.futures.as_completed(future_map.values()):

                for module, f in future_map.items():
                    if f == future:

                        result = future.result()
                        results[module] = result[module]

                        completed += 1
                        percentage = completed / total_modules

                        # ✅ Update module UI
                        progress_bars[module].progress(1.0)
                        module_status[module].success(f"{module} ✅ Completed")

                        # ✅ Update overall progress
                        overall_progress.progress(percentage)

                        break

        st.success("✅ All Selected Modules Executed")

        # ✅ Display Results
        for name, result in results.items():

            st.subheader(f"📌 {name}")

            if name == "Badge Caps":
                st.dataframe(pd.DataFrame(result), use_container_width=True)

            elif name == "Dummy Links":
                st.text(result)

            elif name == "Link Audit":
                if isinstance(result, list):
                    st.dataframe(pd.DataFrame(result), use_container_width=True)
                else:
                    st.error(result)

            elif name == "Form Tester":

                if isinstance(result, dict):

                    df = pd.DataFrame([result])

                    def highlight(row):
                        if row["Result"] == "PASS":
                            return ["background-color: #d4edda"] * len(row)
                        elif row["Result"] == "FAIL":
                            return ["background-color: #f8d7da"] * len(row)
                        else:
                            return ["background-color: #fff3cd"] * len(row)

                    styled_df = df.style.apply(highlight, axis=1)
                    st.dataframe(styled_df, use_container_width=True)

                else:
                    st.error("Unexpected result format")

            elif name == "SEO Meta":

                if isinstance(result, dict):

                    df = pd.DataFrame([result])

                    def highlight(row):
                        if row["Status"] != "OK":
                            return ["background-color: #f8d7da"] * len(row)
                        elif row["Missing ALT Image Count"] > 0:
                            return ["background-color: #fff3cd"] * len(row)
                        else:
                            return ["background-color: #d4edda"] * len(row)

                    styled_df = df.style.apply(highlight, axis=1)
                    st.dataframe(styled_df, use_container_width=True)

                else:
                    st.error("Unexpected result format")