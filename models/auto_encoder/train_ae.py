import pandas as pd
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from joblib import dump

# 1. Load features
df = pd.read_csv('user_features.csv')
X = df[['transaction_count','avg_amount']].values

# 2. Scale
scaler = StandardScaler().fit(X)
Xs = scaler.transform(X)

# 3. Build AE
input_dim = Xs.shape[1]
inputs = keras.Input(shape=(input_dim,))
encoded = keras.layers.Dense(1, activation='relu')(inputs)
decoded = keras.layers.Dense(input_dim, activation='linear')(encoded)
ae = keras.Model(inputs, decoded)
ae.compile(optimizer='adam', loss='mse')

# 4. Train
ae.fit(Xs, Xs, epochs=30, batch_size=8, validation_split=0.1)

# 5. Save model + scaler
ae.save('ae_model.keras')
dump(scaler, 'ae_scaler.joblib')
print("Autoencoder trained and saved.")
