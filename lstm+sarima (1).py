# -*- coding: utf-8 -*-
"""LSTM+SARIMA.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1hoKBUiwOrE5nei-3QE5aG-cgNi5qUJMB
"""

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
import numpy as np
import matplotlib.pyplot as plt

# Load the dataset
file_path = '/content/train (1).csv'
data = pd.read_csv(file_path)

# Convert the 'date' column to datetime format
data['date'] = pd.to_datetime(data['date'])

# Aggregate the sales data by date
sales_data = data.groupby('date')['sales'].sum().reset_index()

# Split the data into training and testing sets
train_size = int(len(sales_data) * 0.8)
train, test = sales_data[:train_size], sales_data[train_size:]

# -----------------------------------
# SARIMA Model
# -----------------------------------

# Define and fit the SARIMA model with optimized parameters
sarima_model = SARIMAX(train['sales'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
sarima_fit = sarima_model.fit(disp=False)

# Make predictions
sarima_pred = sarima_fit.forecast(steps=len(test))

# -----------------------------------
# LSTM Model (Further Improved)
# -----------------------------------

# Prepare the data for LSTM
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(sales_data['sales'].values.reshape(-1, 1))

# Create sequences for LSTM
def create_sequences(data, seq_length):
    sequences = []
    labels = []
    for i in range(len(data) - seq_length):
        sequences.append(data[i:i + seq_length])
        labels.append(data[i + seq_length])
    return np.array(sequences), np.array(labels)

# Sequence length
seq_length = 30

# Create sequences
X, y = create_sequences(scaled_data, seq_length)

# Split into training and testing data
X_train, X_test = X[:train_size - seq_length], X[train_size - seq_length:]
y_train, y_test = y[:train_size - seq_length], y[train_size - seq_length:]

# Build the LSTM model with increased complexity and epochs
lstm_model = Sequential()
lstm_model.add(LSTM(128, return_sequences=True, input_shape=(seq_length, 1)))
lstm_model.add(Dropout(0.25))
lstm_model.add(LSTM(128, return_sequences=True))
lstm_model.add(Dropout(0.25))
lstm_model.add(LSTM(64))
lstm_model.add(Dropout(0.25))
lstm_model.add(Dense(1))

# lstm_model = Sequential()
# lstm_model.add(LSTM(128, return_sequences=True, input_shape=(seq_length, 1)))
# lstm_model.add(BatchNormalization())
# lstm_model.add(Dropout(0.25))
# lstm_model.add(LSTM(128, return_sequences=True))
# lstm_model.add(BatchNormalization())
# lstm_model.add(Dropout(0.25))
# lstm_model.add(LSTM(64))
# lstm_model.add(BatchNormalization())
# lstm_model.add(Dropout(0.25))
# lstm_model.add(Dense(1))

# Compile the model
lstm_model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model for more epochs
lstm_model.fit(X_train, y_train, batch_size=32, epochs=70, verbose=1)

# Make predictions
lstm_pred = lstm_model.predict(X_test)
lstm_pred = scaler.inverse_transform(lstm_pred)

# -----------------------------------
# Ensemble Model (Weighted Average)
# -----------------------------------

# Weighted average of the predictions from SARIMA and LSTM
ensemble_pred = (0.4 * sarima_pred + 0.6 * lstm_pred.flatten())

# Calculate evaluation metrics for the ensemble model
ensemble_mse = mean_squared_error(test['sales'], ensemble_pred)
ensemble_r2 = r2_score(test['sales'], ensemble_pred)

# Binary conversion for classification metrics
threshold = train['sales'].mean()
ensemble_pred_binary = (ensemble_pred > threshold).astype(int)

# Calculate accuracy, precision, and recall
ensemble_accuracy = accuracy_score((test['sales'] > threshold).astype(int), ensemble_pred_binary)
ensemble_precision = precision_score((test['sales'] > threshold).astype(int), ensemble_pred_binary, zero_division=0)
ensemble_recall = recall_score((test['sales'] > threshold).astype(int), ensemble_pred_binary, zero_division=0)
ensemble_f1 = f1_score((test['sales'] > threshold).astype(int), ensemble_pred_binary, zero_division=0)



print(f"Ensemble R² Score: {ensemble_r2}")
print(f"Ensemble Accuracy: {ensemble_accuracy}")
print(f"Ensemble Precision: {ensemble_precision}")
print(f"Ensemble Recall: {ensemble_recall}")
print(f"Ensemble F1 Score: {ensemble_f1}")

# -----------------------------------
# Plotting the Results
# -----------------------------------

# Plot the actual sales
plt.figure(figsize=(14, 7))
plt.plot(sales_data['date'], sales_data['sales'], label='Actual Sales')

# Plot the SARIMA predictions
plt.plot(test['date'], sarima_pred, label='SARIMA Predictions')

# Plot the LSTM predictions
plt.plot(test['date'], lstm_pred.flatten(), label='LSTM Predictions')

# Plot the Ensemble predictions
plt.plot(test['date'], ensemble_pred, label='Ensemble Predictions')

# Formatting the plot
plt.title('Sales Forecasting - Actual vs Predictions')
plt.xlabel('Date')
plt.ylabel('Sales')
plt.legend()
plt.show()

import matplotlib.pyplot as plt

# Metrics for the Ensemble model
metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
values = [ensemble_accuracy, ensemble_precision, ensemble_recall, ensemble_f1]

# Plotting the bar graph
plt.figure(figsize=(8, 6))
plt.bar(metrics, values, color=['blue', 'orange', 'green', 'red'])

# Adding titles and labels
plt.xlabel('Metrics')
plt.ylabel('Scores')
plt.title('Performance Metrics for Ensemble Model')

# Add values on top of bars
for i, value in enumerate(values):
    plt.text(i, value + 0.01, f'{value:.2f}', ha='center', va='bottom')

# Display the plot
plt.ylim(0, 1.1)  # To make sure labels are visible and there's some space above bars
plt.show()

residuals = test['sales'] - ensemble_pred

plt.figure(figsize=(10, 5))
plt.title('Autocorrelation of Ensemble Model Residuals')
plot_acf(residuals, lags=30)
plt.show()

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
plt.figure(figsize=(14, 7))
plt.subplot(121)
plot_acf(train['sales'], lags=30, ax=plt.gca())
plt.title('ACF of Sales Data')

plt.subplot(122)
plot_pacf(train['sales'], lags=30, ax=plt.gca())
plt.title('PACF of Sales Data')
plt.show()

!pip install scikit-learn
!pip install seaborn

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import confusion_matrix, roc_curve, auc # Import necessary functions
import seaborn as sns

conf_matrix = confusion_matrix((test['sales'] > threshold).astype(int), ensemble_pred_binary)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()

# -----------------------------------
# ROC Curve
# -----------------------------------
fpr, tpr, _ = roc_curve((test['sales'] > threshold).astype(int), ensemble_pred)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(10, 7))
plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], 'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend(loc="lower right")
plt.show()