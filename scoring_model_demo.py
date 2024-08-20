import streamlit as st
import plotly.graph_objs as go
import logging
from io import StringIO

# Configure logging to capture logs in a StringIO buffer
log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO)

# Refined grade to score mapping
grade_to_score = {
    'A': 1.0,  # Best score
    'B': 0.5,
    'C': 0.0,  # Neutral score
    'D': -0.5  # Worst score before rejection
}

# Bureau criteria
bureau_criteria = {
    'parameters': [
        'Score',
        'Unsecured Credit enquiries in last 90 days (excluding Invoice Financing / WC enquiries)',
        'Aggregate DPD instances across all open loans in last 6 months',
        'Unsecured No. of Loans disbursed in last 3 months (excluding Invoice Financing / WC loans)',
        'Credit history (1st loan taken and reported in bureau)'
    ],
    'cutoff_criteria': ['< 670 except 0,-1', '10 or More', '6 or More instances', '4 or More new unsecured loans disbursed', 'No Loan history'],
    'responses': ['Reject', 'Reject', 'Reject', 'Reject', 'Restrict LTV to 75%'],
    'grades': {
        'D': ['670-700', '>=10 - 8', 'More than 2', 'More than 2', 'Less than 6m'],
        'C': ['701-730', '7 - <=5', '2', '2', '6m-2yr'],
        'B': ['730-790, 0, -1', '>=4 - 3', '1', '1', '2-5yr, Score 0,-1'],
        'A': ['790 +', '<=2', '0', '0', '>5yr']
    },
    'weightage': 0.13
}

# Invoice Data + GST Data criteria
invoice_criteria = {
    'parameters': [
        'Buyers value contribution in past as per GST Data (Last 12 month)',
        'No of past Invoices on same buyer as per GST Data (Last 12 month)',
        "Buyer's Compliance Score of GST filing (GRC Score)",
        'Borrowers relationship with proposed Buyer as per GST Data (Last 12 month)',
        'Proposed Buyers concentration (No of buyers) as per GST Data (Last 12 month)',
        'Suppliers of Borrower : Aggregate Compliance Score of GST filing (GRC Score)',
        'Proposed Invoice Value to Past 12 month Avg Invoice value of same Buyer',
        'Credit period offered',
        'HSN Code of Invoice Item : HSN code of last 12M invoices of same buyer'
    ],
    'cutoff_criteria': ['Nil', 'First timer', 'GRC Score less than 50%', 'First timer', 'Single Buyer', 'None', 'More than 60% variance', 'More than 180 days', 'No Match'],
    'responses': ['Restrict LTV to 50%', 'Restrict LTV to 50%', 'Restrict LTV to 50%', 'Restrict LTV to 50%', 'Restrict LTV to 50%', 'Restrict LTV to 50%', 'Reject', 'Restrict LTV to 50%'],
    'grades': {
        'D': ['Less than 50%', 'First Timer / Non significant', '<70%', '<6m', '<=3', '<70%', 'More than 50%', 'More than 120 days', 'Less than 20%'],
        'C': ['Top 50% - Top 20%', 'Top 50% - Top 20%', '70%-80%', '>6m - 1yr', '>3 <=5', '70%-80%', '30% -50% variance', '90-120 days', '20%-50%'],
        'B': ['Top 20% - Top10%', 'Top 20% - Top10%', '80%-90%', '>1 - 2yr', '6 - <=10', '80%-90%', '20%-30% variance', '60-90 days', '50%-75%'],
        'A': ['Top 10%', 'Top 10%', '>90%', '> 2yr', '>10', '>90%', 'Less than 20% variance', 'Upto 60 days', 'Amongst more than 75% of past invoice value']
    },
    'weightage': 0.15
}

# Bank Statement Data criteria
bank_criteria = {
    'parameters': [
        'Sum Total of Bank credits of last 12m / GST Turnover last 12m',
        'Cheque / ECS / NACH returns (Funds Insufficient/Exceed arrangement) in last 12m',
        'Invoice amount / Daily Average balance'
    ],
    'cutoff_criteria': ['Below 50%', 'More than 18 returns', '<20x'],
    'responses': ['Reject', 'Reject', 'Reject'],
    'grades': {
        'D': ['Less than 60%', '>10x', '>10x'],
        'C': ['60-75%', '>6 <=10', '>3x - 10x'],
        'B': ['70-85%', '>3 <=6', '>1x-3x'],
        'A': ['>85%', '0-3', '>1x']
    },
    'weightage': 0.1
}

# Borrower Data + GST Data criteria
borrower_criteria = {
    'parameters': [
        'Borrower GST Compliance score (GRC score)',
        'Business vintage : GST registration date'
    ],
    'cutoff_criteria': ['Less than 70', 'Less than 6 months'],
    'responses': ['Restrict LTV to 50%', 'Restrict LTV to 50%'],
    'grades': {
        'D': ['<70%', '> 6m & < 12m'],
        'C': ['70%-80%', '1-2yr'],
        'B': ['80%-90%', '2-3yr'],
        'A': ['>90%', '>3yr']
    },
    'weightage': 0.12
}

# Function to calculate the credit score with logging
def calculate_score_refined_with_logging(input_data):
    final_score = 0

    sections = {
        'bureau': bureau_criteria,
        'invoice': invoice_criteria,
        'bank': bank_criteria,
        'borrower': borrower_criteria
    }

    for section, criteria in sections.items():
        section_score = 0
        for i, param in enumerate(criteria['parameters']):
            value = input_data.get(param, None)

            if value is None:
                logging.info(f"{param} missing, assigning default score for grade 'C'")
                section_score += grade_to_score['C'] * criteria['weightage']
                continue

            if value in criteria['cutoff_criteria']:
                response = criteria['responses'][criteria['cutoff_criteria'].index(value)]
                if response == 'Reject':
                    logging.info(f"{param} value '{value}' triggers rejection")
                    return "Application Rejected"
                elif 'Restrict LTV' in response:
                    logging.info(f"{param} value '{value}' triggers LTV restriction: {response}")
                    continue

            for grade, grade_values in criteria['grades'].items():
                if value in grade_values:
                    logging.info(f"{param} value '{value}' matches grade '{grade}'")
                    section_score += grade_to_score[grade] * criteria['weightage']
                    break

        final_score += section_score

    final_score_rounded = round(final_score, 2)
    logging.info(f"Final calculated score: {final_score_rounded}")
    return final_score_rounded

# Streamlit UI
st.title("🧮 Credit Underwriting Scoring Model Demo")

st.markdown("""
Welcome to the Credit Underwriting Scoring Model demo. Adjust the parameters below to see how they impact the credit score.
This model helps to determine the creditworthiness of MSME business loans based on various data points.
""")

# Section for user inputs
st.header("Input Parameters")

# Bureau Data Inputs
st.subheader("📊 Bureau Data")
score = st.selectbox("Score",
                     ['790 +', '730-790, 0, -1', '670-700', '< 670 except 0,-1'],
                     help="The overall credit score from the credit bureau. Higher scores indicate better credit history.")
credit_enquiries = st.selectbox("Unsecured Credit enquiries in last 90 days",
                                ['<=2', '7 - <=5', '10 or More'],
                                help="Number of unsecured credit inquiries made in the last 90 days.")
dpd_instances = st.selectbox("Aggregate DPD instances across all open loans in last 6 months",
                             ['0', '2', 'More than 2'],
                             help="The number of days past due (DPD) across all open loans in the last 6 months.")
loans_disbursed = st.selectbox("Unsecured No. of Loans disbursed in last 3 months",
                               ['0', '2', 'More than 2'],
                               help="Number of unsecured loans disbursed in the last 3 months.")
credit_history = st.selectbox("Credit history (1st loan taken and reported in bureau)",
                              ['>5yr', '2-5yr', '6m-2yr', 'Less than 6m'],
                              help="Length of credit history as reported by the credit bureau.")

# Invoice Data + GST Data Inputs
st.subheader("🧾 Invoice Data + GST Data")
buyer_value = st.selectbox("Buyers value contribution in past as per GST Data (Last 12 month)",
                           ['Top 10%', 'Top 20% - Top10%', 'Top 50% - Top 20%', 'Less than 50%'],
                           help="Contribution of buyers' value in the past 12 months as per GST data.")
compliance_score = st.selectbox("Buyer's Compliance Score of GST filing (GRC Score)",
                                ['>90%', '80%-90%', '70%-80%', '<70%'],
                                help="Compliance score of the buyer's GST filings.")
invoice_value_variance = st.selectbox("Proposed Invoice Value to Past 12 month Avg Invoice value of same Buyer",
                                      ['Less than 20% variance', '20%-30% variance', '30% -50% variance', 'More than 50%'],
                                      help="Variance between the proposed invoice value and the average invoice value of the same buyer in the last 12 months.")

# Bank Statement Data Inputs
st.subheader("🏦 Bank Statement Data")
bank_credits = st.selectbox("Sum Total of Bank credits of last 12m / GST Turnover last 12m",
                            ['>85%', '70-85%', '60-75%', 'Less than 60%'],
                            help="Total bank credits in the last 12 months as a percentage of GST turnover.")
cheque_returns = st.selectbox("Cheque / ECS / NACH returns (Funds Insufficient/Exceed arrangement) in last 12m",
                              ['0-3', '>3 <=6', '>6 <=10', '>10x'],
                              help="Number of cheque/ECS/NACH returns due to insufficient funds in the last 12 months.")
invoice_balance = st.selectbox("Invoice amount / Daily Average balance",
                               ['>1x', '>1x-3x', '>3x - 10x', '>10x'],
                               help="Ratio of invoice amount to daily average balance.")

# Borrower Data + GST Data Inputs
st.subheader("🧑‍💼 Borrower Data + GST Data")
borrower_compliance = st.selectbox("Borrower GST Compliance score (GRC score)",
                                   ['>90%', '80%-90%', '70%-80%', '<70%'],
                                   help="Borrower's GST compliance score.")
business_vintage = st.selectbox("Business vintage : GST registration date",
                                ['>3yr', '2-3yr', '1-2yr', '> 6m & < 12m'],
                                help="Age of the business based on GST registration date.")

# Combine all inputs into a dictionary
inputs = {
    'Score': score,
    'Unsecured Credit enquiries in last 90 days (excluding Invoice Financing / WC enquiries)': credit_enquiries,
    'Aggregate DPD instances across all open loans in last 6 months': dpd_instances,
    'Unsecured No. of Loans disbursed in last 3 months (excluding Invoice Financing / WC loans)': loans_disbursed,
    'Credit history (1st loan taken and reported in bureau)': credit_history,
    'Buyers value contribution in past as per GST Data (Last 12 month)': buyer_value,
    "Buyer's Compliance Score of GST filing (GRC Score)": compliance_score,
    'Proposed Invoice Value to Past 12 month Avg Invoice value of same Buyer': invoice_value_variance,
    'Sum Total of Bank credits of last 12m / GST Turnover last 12m': bank_credits,
    'Cheque / ECS / NACH returns (Funds Insufficient/Exceed arrangement) in last 12m': cheque_returns,
    'Invoice amount / Daily Average balance': invoice_balance,
    'Borrower GST Compliance score (GRC score)': borrower_compliance,
    'Business vintage : GST registration date': business_vintage
}

# Button to calculate the score
if st.button("Calculate Score"):
    score = calculate_score_refined_with_logging(inputs)
    st.write(f"### 📈 Calculated Credit Score: {score}")

    if isinstance(score, str) and score == "Application Rejected":
        st.write("### 🚫 The application is rejected based on the provided inputs.")
    else:
        # Display a pie chart of the score components (placeholder values for sections)
        labels = ['Bureau Data', 'Invoice Data + GST Data', 'Bank Statement Data', 'Borrower Data + GST Data']
        values = [20, 30, 25, 25]  # These values should be dynamically calculated based on actual score breakdowns
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        st.plotly_chart(fig)

    # Show detailed logs
    st.write("#### Detailed Analysis:")
    log_output = log_stream.getvalue()
    st.text(log_output)

    # Clear log stream after displaying
    log_stream.truncate(0)
    log_stream.seek(0)

# To run this, save the file and use `streamlit run scoring_model_demo.py`
