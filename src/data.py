import pandas as pd
import numpy as np
import json

# Variables
FILE_PATH = "data/problemas_planes.xlsx"
SAVE_PATH = "data/processed"


def load_data(file_path=FILE_PATH) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads data from an Excel file and returns two pandas DataFrames.

    Parameters
    ----------
    file_path : str
        Path to the Excel file.

    Returns
    -------
    tuple
        A tuple containing two pandas DataFrames. The first DataFrame represents
        the needs data and the second DataFrame represents the plans data.

    Examples
    --------
    >>> needs, plans = load_data()
    >>> needs.head()
    >>> plans.head()
    """

    # Autodetects sheet names
    xl = pd.ExcelFile(file_path)
    needs_sheet = [h for h in xl.sheet_names if "neces" in h.lower()][0]
    plans_sheet = [
        h for h in xl.sheet_names if "catalog" in h.lower() or "plan" in h.lower()
    ][0]

    # Reeads sheets
    needs_all_df = pd.read_excel(file_path, sheet_name=needs_sheet)
    plans_df = pd.read_excel(file_path, sheet_name=plans_sheet)

    # DataFrame of needs with realtions with plans
    cod_nec = search_column(plans_df, "código problema")
    desc_nec = search_column(plans_df, "necesidad")
    cod_plan = search_column(plans_df, "código plan")

    needs_with_true_plans = set(plans_df.loc[plans_df[cod_plan].notna(), cod_nec])
    needs_df = (
        plans_df[[cod_nec, desc_nec]]
        .drop_duplicates()
        .dropna(subset=[cod_nec])
        .reset_index(drop=True)
    )
    needs_df = needs_df[needs_df[cod_nec].isin(needs_with_true_plans)].copy()
    needs_df = needs_df.merge(
        needs_all_df[[cod_nec, "Urgencia", "Importancia"]], on=cod_nec, how="left"
    )

    # Select important columns only
    plans_df = plans_df.iloc[:, 2:]

    # Transforms columns to numeric values
    urgency_map = {"Menos urgente": 1, "Urgente": 2, "Muy urgente": 3}
    needs_df.iloc[:, -2] = needs_df.iloc[:, -2].map(urgency_map)

    importance_map = {"Menos importante": 1, "Importante": 2, "Muy importante": 3}
    needs_df.iloc[:, -1] = needs_df.iloc[:, -1].map(importance_map)

    complexity_map = {"Sencillo": 1, "Complejo": 2, "Muy  complejo": 3}
    plans_df.iloc[:, -1] = plans_df.iloc[:, -1].map(complexity_map)

    plans_df["Plazo"] = (
        plans_df["Plazo de ejecución"].str.extract(r"(\d+)").astype(float)
    )
    plans_df.drop(columns=["Plazo de ejecución"], inplace=True)

    plans_df = fillna_mode_for_columns(
        plans_df, ["Complejidad"], valid_values={1, 2, 3}
    )
    plans_df = fillna_mode_for_columns(plans_df, ["Plazo"])
    needs_df = fillna_mode_for_columns(
        needs_df, ["Urgencia", "Importancia"], valid_values={1, 2, 3}
    )

    return needs_df, plans_df


def search_column(df: pd.DataFrame, word: str) -> str | None:
    """
    Searches for a column name in a pandas DataFrame that contains a given
    word (case-insensitive).

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to search for the column name.
    word : str
        Word to search for in the column names.

    Returns
    -------
    str or None
        The column name that contains the given word, or None if no
        column name contains the word.
    """

    return next((c for c in df.columns if word.lower() in c.lower()), None)


def fillna_mode_for_columns(df, columns, valid_values=None):
    """
    Fills NaN and zero values in the specified columns using the mode of valid values (optionally restricted).

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to modify.
    columns : list[str]
        List of column names to fill.
    valid_values : set, optional
        Set of valid values to consider for the mode (e.g., {1, 2, 3}).

    Returns
    -------
    pd.DataFrame
        The same DataFrame, with the specified columns processed.
    """

    for col in columns:
        coldata = df[col]
        # Filter only the valid values for mode calculation
        if valid_values is not None:
            valid = coldata[coldata.isin(valid_values)]
        else:
            valid = coldata.dropna()
        # Compute the mode
        if not valid.empty:
            mode_val = valid.mode().iloc[0]
        else:
            mode_val = 1  # Safe default
        # Fill NaN and replace zeros with the mode
        df[col] = (
            coldata.fillna(mode_val)
            .replace(0, mode_val)
            .infer_objects(copy=False)
            .astype(int)
        )

    return df


def extract_needs(needs: pd.DataFrame) -> dict:
    """
    Extracts relevant information from a DataFrame containing needs data.

    Parameters
    ----------
    needs : pandas.DataFrame
        DataFrame containing needs data.

    Returns
    -------
    dict
        A dictionary with the needs data.

    Examples
    --------
    >>> needs_df_processed, needs_dict = extract_needs(needs_df)
    """

    col_nec_code = search_column(needs, "código")
    col_urgency = search_column(needs, "urgencia")
    col_importance = search_column(needs, "importancia")
    col_problem = search_column(needs, "necesidad") or search_column(needs, "problema")

    needs_df_processed = needs[
        [col_nec_code, col_problem, col_urgency, col_importance]
    ].dropna(subset=[col_nec_code])

    needs_dict = {
        row[col_nec_code]: {
            "necesidad": row[col_problem],
            "urgencia": row[col_urgency],
            "importancia": row[col_importance],
        }
        for _, row in needs_df_processed.iterrows()
    }

    return needs_dict


def extract_plans_and_relations(plans: pd.DataFrame) -> tuple[dict, dict]:
    """
    Extracts relevant information from a DataFrame containing plans data.

    Parameters
    ----------
    plans : pandas.DataFrame
        DataFrame containing plans data.

    Returns
    -------
    tuple
        A tuple containing two dictionaries. The first dictionary contains
        the plans data and the second dictionary contains the relations
        between needs and plans.

    Examples
    --------
    >>> plans_df_processed, need_plan_relation = extract_plans_and_relations(plans_df)
    >>> plans_df_processed.head()
    >>> need_plan_relation
    """

    col_plan_cod = search_column(plans, "código plan")
    col_plan_desc = search_column(plans, "descripción")
    col_period = search_column(plans, "plazo")
    col_complexity = search_column(plans, "complejidad")
    col_plan_need_cod = search_column(plans, "código problema")

    plans_df_processed = plans[
        [col_plan_cod, col_plan_desc, col_period, col_complexity, col_plan_need_cod]
    ].dropna(subset=[col_plan_cod])

    plans_dict = {
        row[col_plan_cod]: {
            "descripcion": row[col_plan_desc],
            "plazo_ejecucion": row[col_period],
            "complejidad": row[col_complexity],
            "codigo_problema": row[col_plan_need_cod],
        }
        for _, row in plans_df_processed.iterrows()
    }

    need_plan_relation = {}
    for _, row in plans_df_processed.iterrows():
        codigo_problema = row[col_plan_need_cod]
        codigo_plan = row[col_plan_cod]
        if pd.notnull(codigo_problema):
            need_plan_relation.setdefault(codigo_problema, []).append(codigo_plan)

    return plans_dict, need_plan_relation


def save_json(needs: dict, plans: dict, relations: dict, path: str) -> None:
    """
    Saves the given needs, plans and relations to three JSON files.

    Parameters
    ----------
    needs : dict
        A dictionary containing the needs data.
    plans : dict
        A dictionary containing the plans data.
    relations : dict
        A dictionary mapping need codes to lists of associated plan codes.
    path : str
        The path to save the JSON files to.

    Returns
    -------
    None
    """

    with open(f"{path}_necesidades.json", "w") as f:
        json.dump(needs, f)

    with open(f"{path}_planes.json", "w") as f:
        json.dump(plans, f)

    with open(f"{path}_relacion_necesidad_plan.json", "w") as f:
        json.dump(relations, f)


if __name__ == "__main__":
    needs_df, plans_df = load_data(FILE_PATH)

    # print(needs_df.head())
    # print(plans_df.head())

    needs_dict = extract_needs(needs_df)
    plans_dict, relations_dict = extract_plans_and_relations(plans_df)

    save_json(needs_dict, plans_dict, relations_dict, SAVE_PATH)
