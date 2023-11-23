
from flask import Flask, request
from tabula.io import read_pdf
import pandas as pd
import re

app = Flask(__name__)


def clean_rows(df):
    _df = df.copy()
    _df['Transaction ID'] = ''
    for i in range(0, len(_df)-1, 2):
        tx = _df.loc[i, 'Date'].split()
        _df.loc[i, 'Transaction ID'] = _df.loc[i +
                                               1, 'Date'].replace("REF NO:. ", "")
        _df.loc[i, 'Date'] = " ".join(tx[:2])
        _df.loc[i, 'TX'] = " ".join(tx[2:])
        _df.loc[i, 'Amt'] = float(_df.loc[i, 'Amt'].split(
        )[0]) * (-1 if _df.loc[i, 'Amt'].split()[1] == 'DB' else 1)

    _df = _df.dropna().reset_index(drop=True)
    _df = _df.query(
        'TX != "SEND MONEY TO MY ACCOUNT" and TX != "TOP UP WALLET FROM MY ACCOUNT"')
    return _df


def clean_first(_df):
    df_0 = _df[0].copy()

    df_0 = df_0.drop(index=range(0, 9))
    df_0 = df_0.drop(index=df_0.index[-1])
    df_0.columns = ["Date", "TX", "Amt"]

    df_0 = df_0.reset_index(drop=True)

    df_0 = clean_rows(df_0)

    return df_0


def clean_last(_df):
    df_l = _df[-1].copy()
    df_l = df_l.drop(columns=['Unnamed: 0'])
    df_l.columns = ["Date", "TX", "Amt"]

    df_l = df_l.drop(df_l.index[-19:])
    df_l = clean_rows(df_l)

    return df_l


def clean_rest(df):
    _df_a = pd.DataFrame([])
    for _df in df[1:-1]:
        _df.columns = ['Date', 'TX', 'Amt']
        _df = _df.drop(_df.index[-1])
        _df['Transaction ID'] = ''
        for i in range(0, len(_df)-1, 2):
            _df.loc[i, 'Transaction ID'] = _df.loc[i +
                                                   1, 'TX'].replace("REF NO:. ", "")
            _df.loc[i, 'Amt'] = float(_df.loc[i, 'Amt'].split(
            )[0]) * (-1 if _df.loc[i, 'Amt'].split()[1] == 'DB' else 1)
        _df = _df.dropna().reset_index(drop=True)
        _df = _df.query(
            'TX != "SEND MONEY TO MY ACCOUNT" and TX != "TOP UP WALLET FROM MY ACCOUNT"')
        _df.reset_index(drop=True)
        _df_a = pd.concat([_df_a, _df], ignore_index=True)
    _df_a = _df_a.reset_index(drop=True)
    return _df_a


@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    # Check if a file is present in the request
    if 'file' not in request.files:
        return 'No file found', 400

    file = request.files['file']

    # Check if the file is a PDF
    if file.filename.endswith('.pdf'):
        # Process the PDF file here
        # You can use a library like Tabula to extract data from the PDF
        df_test = read_pdf(file, pages="all", lattice=False, encoding="utf-8", stream=False,
                           area=(100, 0, 2000, 2000))

        df_test_0 = clean_first(df_test)
        # df_test_l = clean_last(df_test)
        # df_test_r = clean_rest(df_test)

        last_page = False
        for index, row in df_test[-1].iterrows():
            if row.str.contains("REF NO:.", na=False).any():
                last_page = True
                break

        _df_a = pd.DataFrame([])
        if last_page:
            df1_l = clean_last(df_test)
            df1_r = clean_rest(df_test)

            _df_a = pd.concat([df_test_0, df1_r, df1_l], ignore_index=True)
            _df_a = _df_a.reset_index(drop=True)
            print(_df_a)
        else:
            for _df in df_test[1:-2]:
                # print(_df)
                _df = _df.dropna(axis=1, how='all')
                _df.columns = ['Date', 'TX', 'Amt']
                _df['Transaction ID'] = ''
                last_row = 0
                for index, row in _df.iterrows():
                    if row.str.contains("REF NO:", na=False).any():
                        last_row = index
                _df = _df.drop(_df.index[last_row+1:])
                for i in range(0, len(_df)-1, 2):
                    if re.match(r"^\d{2} [A-Z][a-z]{3}.+", _df.loc[i, 'Date']):
                        _df.loc[i, 'TX'] = " ".join(
                            _df.loc[i, 'Date'].split()[2:])
                        _df.loc[i, 'Date'] = " ".join(
                            _df.loc[i, 'Date'].split()[:2])
                    _df.loc[i, 'Transaction ID'] = _df.loc[i +
                                                           1, 'TX'].replace("REF NO:. ", "")
                    _df.loc[i, 'Amt'] = float(_df.loc[i, 'Amt'].split(
                    )[0]) * (-1 if _df.loc[i, 'Amt'].split()[1] == 'DB' else 1)
                _df = _df.dropna().reset_index(drop=True)
                _df = _df.query(
                    'TX != "SEND MONEY TO MY ACCOUNT" and TX != "TOP UP WALLET FROM MY ACCOUNT"')
                _df.reset_index(drop=True)
                _df_a = pd.concat([_df_a, _df], ignore_index=True)
                _df_a = _df_a.reset_index(drop=True)
            _df_a = _df_a.reset_index(drop=True)
            print(_df_a)

        df_test_final = pd.concat([df_test_0, _df_a], ignore_index=True)

        # Convert dataframe to JSON-suitable format
        df_test_final_json = df_test_final.to_json(orient='records')

        # Return the JSON-suitable format
        return df_test_final_json
    else:
        return 'Invalid file format. Only PDF files are allowed', 400


if __name__ == '__main__':
    app.run(port=9119, host='0.0.0.0')
