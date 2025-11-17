%% 🌎 Environmental Justice Index (EJI) Data Cleaning — MATLAB Helper Code
% (This code is for anyone copying the main github code in order to run it
%   with other years of data in their own app)
%
% This MATLAB script cleans Environmental Justice Index (EJI) data 
% downloaded from the CDC and prepares it for use in the GitHub/Streamlit app.
%
% ⚠️ IMPORTANT:
% The Streamlit app is designed to view and prioritize **New Mexico data** 
% from a single year and compare it to other metrics from that same year 
% — not between different years.
%
% -------------------------------------------------------------------------
% 🧩 HOW TO USE THIS CODE
%
% 1️⃣ Download EJI data (CSV format) from the CDC website:
%     👉 https://www.atsdr.cdc.gov/place-health/php/eji/eji-data-download.html
%
%     If you don't trust the link, search "EJI CDC data download" and 
%     click on: **EJI Data Download | Place and Health | ATSDR**
%
%     Once on the page:
%       • Under **"Year"**, choose the year you want.
%       • Under **"Geography"**, choose **United States**.
%       • Under **"File Type"**, select **CSV File**.
%       • Click the **"Go"** button — this downloads a ZIP folder.
%
% 2️⃣ Locate your downloaded dataset:
%       • It's probably in your **Downloads** folder.
%       • The file will look like:  EJI_2024_United_States_CSV.zip
%
%     💡 How to find it:
%       - On Windows: Press **Windows + E**, click **Downloads**.
%       - On Mac: Open **Finder**, select **Downloads** in the sidebar.
%       - On Chrome: Click the small arrow next to the downloaded file and
%         choose **"Show in folder"**.
%
% 3️⃣ Unzip (extract) the file:
%       • Right-click → "Extract All…" (Windows)  
%         or double-click/open with Archive Utility (Mac).
%       • Inside, you'll see a file named like:
%         EJI_2024_United_States.csv
%
% 4️⃣ Move or drag that CSV file into your MATLAB workspace.
%       • You can also use the **Current Folder** panel in MATLAB to navigate
%         to your Downloads folder and double-click the CSV to load it.
%
% 5️⃣ Check your MATLAB Workspace:
%       • You should now see a variable name like:
%           EJI_2023_United_States  or  EJI_2025_United_States
%
% 6️⃣ Update this code to match your file name:
%       • Press **Ctrl + H** (Cmd + H on Mac) to open Find & Replace.
%       • In "Find what":     EJI_2024_United_States
%       • In "Replace with":  your actual dataset name.
%       • Click **Replace All**.
%
% 7️⃣ Run this script to automatically:
%       ✅ Clean and simplify the dataset
%       ✅ Replace missing (-999) values with NaN
%       ✅ Compute state-level averages
%       ✅ Compute county-level averages for New Mexico
%       ✅ Save clean CSV files ready for your Streamlit app
%
% -------------------------------------------------------------------------
% ✨ OUTPUT FILES:
%   • EJI_StateAverages_RPL.csv          (clean state-level data)
%   • EJI_NewMexico_CountyMeans.csv      (clean county-level NM data)
%
% These can be uploaded directly into your GitHub files to visualize other
% years of EJI data in the Streamlit app
%
% -------------------------------------------------------------------------
%% --- Step 1: Rename your workspace variable for convenience ---
data = EJI_2024_United_States;

%% --- Step 2: Keep only needed columns ---
keyCols = {'StateDesc', 'COUNTY', 'RPL_EJI', 'RPL_EBM', 'RPL_SVM', 'RPL_HVM', 'RPL_CBM', 'RPL_EJI_CBM'};
keyCols = intersect(keyCols, data.Properties.VariableNames, 'stable')
data = data(:, keyCols);

%% --- Step 3: Replace -999 with NaN ---
for i = 3:width(data)
    data.(i)(data.(i) == -999) = NaN;
end

%% --- Step 4: Compute STATE-LEVEL AVERAGES ---
stateSummary = groupsummary(data, "StateDesc", "mean", keyCols(3:end), 'IncludeEmptyGroups', false);
stateSummary.Properties.VariableNames

stateSummary.Properties.VariableNames = {'State', 'GroupCount', 'Mean_EJI', 'Mean_EBM', 'Mean_SVM', 'Mean_HVM', 'Mean_CBM', 'Mean_EJI_CBM'};
% Remove the numbering column if it exists (often the first one)
if strcmp(stateSummary.Properties.VariableNames{1}, 'GroupCount') || isnumeric(stateSummary{:,1})
    stateSummary(:, 1) = [];
end

% Remove GroupCount column if it still exists
if any(strcmp(stateSummary.Properties.VariableNames, 'GroupCount'))
    stateSummary.GroupCount = [];
end

% Write clean version
writetable(stateSummary, 'EJI_StateAverages_RPL.csv');
% Display top rows
disp(stateSummary(1:10,:));

%% --- Step 5: Compute NEW MEXICO COUNTY AVERAGES ---
% Assuming your main table is called EJI_2024_United_States
% and is already loaded in the workspace

% Convert StateDesc to string to ensure proper matching
EJI_2024_United_States.StateDesc = string(EJI_2024_United_States.StateDesc);

% Filter for only New Mexico rows
nmData = EJI_2024_United_States(EJI_2024_United_States.StateDesc == "New Mexico", :);

% Check how many rows we got
disp("Number of rows for New Mexico:");
disp(height(nmData));

% Replace -999 values with NaN
nmData = standardizeMissing(nmData, -999);

% Group by county and calculate mean of relevant fields
countySummary = groupsummary(nmData, "COUNTY", "mean", ...
    ["RPL_EJI", "RPL_EBM", "RPL_SVM", "RPL_HVM", "RPL_CBM", "RPL_EJI_CBM"]);

% Rename columns to cleaner labels
countySummary.Properties.VariableNames = {'County','GroupCount','Mean_EJI','Mean_EBM','Mean_SVM','Mean_HVM','Mean_CBM','Mean_EJI_CBM'};
% Remove the numbering column if it exists
if strcmp(countySummary.Properties.VariableNames{1}, 'GroupCount') || isnumeric(countySummary{:,1})
    countySummary(:, 1) = [];
end

% Remove GroupCount column if it still exists
if any(strcmp(countySummary.Properties.VariableNames, 'GroupCount'))
    countySummary.GroupCount = [];
end

% Write clean version
writetable(countySummary, 'EJI_NewMexico_CountyMeans.csv');

% Display top rows
disp(countySummary(1:10,:));
