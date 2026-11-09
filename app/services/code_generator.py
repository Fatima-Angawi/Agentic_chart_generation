import os
from openai import OpenAI
from app.services.profiler import get_profile_data

def generate_chart_code(model, df, user_instructions, out_path_v1):
  schema = get_profile_data(df)
  schema_description = "\n".join([f"- {col} ({dtype})" for col, dtype in schema.items()])

  client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

  prompt = f"""you are a data visualisation expert
  Return your answer *strictly* in this format:

    <execute_python>
    # valid python code here
    </execute_python>

    Do not add explanations, only the tags and the code.
    you will creat a chart generation code given dataframe columns and types:{schema_description} and user instructions:{user_instructions}

    required:
    1. Assume the DataFrame is already loaded as 'df'.
    2. Use matplotlib for plotting.
    3. Add clear title, axis labels, and legend if needed.
    4. Save the figure as '{out_path_v1}' with dpi=300.
    5. Do not call plt.show().
    6. Close all plots with plt.close().
    7. Add all necessary import python statements
       Filter by year/quarter using the 'year' and 'quarter' integer columns.
    8. Do NOT use ax.bar_label / plt.bar_label. If you want value labels, use ax.text with f-strings.
    9. Only use plain format strings such as f"{{v:,.0f}}" (no spaces inside the format specifier).
    10. Stick to basic, widely supported matplotlib functions (bar, plot, legend, title, xlabel, ylabel, tight_layout, savefig).


    Return ONLY the code wrapped in <execute_python> tags.
    """

  response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1
    )

  return response.choices[0].message.content
