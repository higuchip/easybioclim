# easybioclim User Manual

Welcome to easybioclim! This application allows you to easily obtain bioclimatic data for specific geographical points of interest.

## How it Works

easybioclim streamlines the process of accessing and analyzing bioclimatic variables using a simple, interactive interface. Here's a step-by-step guide to using the application:

1.  **Select Points of Interest:** Use the interactive map to click and select the geographical locations for which you want to retrieve bioclimatic data.
2.  **Export Points:** Once you have selected your desired points, export them as a GeoJSON file. This file contains the geographical coordinates of your selected locations.
3.  **Upload GeoJSON:** Upload the exported GeoJSON file back into the application.
4.  **Name Your Points:** Provide meaningful names or identifiers for each of your selected points. This will help you organize and interpret the results.
5.  **Fetch Bioclimatic Data:** The application will then connect to Google Earth Engine and retrieve 19 different bioclimatic variables from the WorldClim dataset for each of your specified points.
6.  **View and Download Results:** The fetched bioclimatic data will be displayed in a clear, tabular format. You can then download this data as a CSV file for further analysis or record-keeping.

## Key Features and Technologies

easybioclim leverages several powerful open-source libraries and platforms to provide a seamless user experience:

*   **Streamlit:** Powers the interactive web interface, making it easy to use and navigate.
*   **Geemap & Folium:** Enable the display of interactive maps for point selection.
*   **Google Earth Engine:** Provides access to the comprehensive WorldClim bioclimatic dataset and handles the data processing.
*   **GeoPandas:** Efficiently manages and processes the geospatial data (your selected points).
*   **Pandas:** Used for organizing and manipulating the fetched bioclimatic data into a user-friendly table.

We hope you find easybioclim useful for your research and data analysis needs!

## Repository File Summary

This section provides a brief overview of the key files in the easybioclim repository:

*   **`app.py`**: This is the core of the application. It's a Python script that uses the Streamlit library to create the web interface you interact with. It handles map displays, file uploads (your GeoJSON), text inputs for naming points, fetching data from Google Earth Engine, processing data with Pandas and GeoPandas, and enabling the download of your results.
*   **`README.md`**: A short introductory file (written in Portuguese). It states the application's name ("easybioclim") and its main goal: to provide a web app for obtaining bioclimatic data for points of interest.
*   **`Pipfile`**: Used by the Pipenv tool to manage the Python libraries (dependencies) needed for easybioclim to run. It lists packages like Streamlit, GeoPandas, Geemap, Google Earth Engine (ee), and Pandas.
*   **`Pipfile.lock`**: An auto-generated file that works with `Pipfile`. It records the exact versions of all dependencies, ensuring that if you set up the project elsewhere, it will use the same package versions for consistency.
*   **`.gitignore`**: A standard Git configuration file. It tells Git which files or directories to ignore (e.g., temporary files, local configuration, virtual environment folders) so they aren't accidentally included in the project's version history.

## Potential Improvements and Next Steps

This section outlines potential enhancements and future development directions for easybioclim:

1.  **Enhance `README.md`**:
    *   **Detailed Usage Instructions**: The main `README.md` could be significantly improved. It should ideally include:
        *   A clear, concise English description of the project.
        *   Step-by-step instructions on how to run the application locally (e.g., cloning, installing dependencies with Pipenv, running the Streamlit command).
        *   A more detailed explanation of the bioclimatic variables (perhaps linking to the WorldClim documentation or the table already in the app).
        *   A GIF or screenshots demonstrating the app's functionality.
    *   **Contribution Guidelines**: If contributions are welcome, add a section on how to contribute.
    *   **License Information**: Add a `LICENSE` file and refer to it in the README.

2.  **Application Enhancements**:
    *   **Error Handling and User Feedback**: Implement more robust error handling (e.g., for file upload issues, problems with GEE data fetching, incorrect GeoJSON format) and provide clearer feedback messages to the user within the Streamlit app.
    *   **Internationalization (i18n)**: The UI text (titles, captions, warnings) in `app.py` is in Portuguese. If the app is intended for a broader audience, consider internationalizing it by supporting multiple languages, including English.
    *   **Input Validation**: Add validation for user inputs, such as the area identification list, to ensure it matches the number of points in the GeoJSON.
    *   **Direct Point Drawing on Map (if feasible)**: The current workflow requires users to draw points, export, and then re-upload. While this uses `geemap`'s built-in export, exploring if Streamlit or Folium could directly capture drawn coordinates into the Python backend without the export/upload step could streamline the UX. This might be complex but worth investigating.
    *   **Configuration for Bioclimatic Variables**: Allow users to select which bioclimatic variables they are interested in, rather than always fetching all 19.
    *   **Styling and UI/UX**: Further refine the UI for better aesthetics and user experience.

3.  **Development and Maintenance**:
    *   **Code Comments and Docstrings**: Add more comments and docstrings to `app.py` to explain complex functions and logic, improving maintainability.
    *   **Unit Tests**: Implement unit tests for key functions, especially data processing and transformations, to ensure reliability and catch regressions.
    *   **Dependency Management**: Keep dependencies in `Pipfile` updated.
