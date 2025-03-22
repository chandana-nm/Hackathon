"""
Sign language recognition model implementation.
This module handles the machine learning model for sign language detection.
"""
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import os
import pickle

class SignLanguageModel:
    def __init__(self):
        # Model parameters
        self.num_landmarks = 21  # MediaPipe hand landmarks
        self.num_coords = 3      # x, y, z coordinates
        self.sequence_length = 30  # Frames per sign
        self.classes = ['one', 'two', 'three', 'four', 'five']  # Signs to detect
        
        # Paths
        self.model_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, 'sign_language_model.h5')
        self.scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
        
        # Load model if exists
        if os.path.exists(self.model_path):
            print(f"Loading model from {self.model_path}")
            self.model = load_model(self.model_path)
            
            # Load scaler if exists
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            else:
                self.scaler = None
        else:
            print("No existing model found. Initialize with create_model()")
            self.model = None
            self.scaler = None
    
    def preprocess_landmarks(self, landmarks_sequence):
        """Normalize and preprocess hand landmarks"""
        # Convert to list if it's a numpy array
        if isinstance(landmarks_sequence, np.ndarray):
            landmarks_sequence = landmarks_sequence.tolist()
        
        # Ensure we have the right number of frames
        if len(landmarks_sequence) < self.sequence_length:
            # Pad with the last frame
            last_frame = landmarks_sequence[-1]
            landmarks_sequence = landmarks_sequence + [last_frame] * (self.sequence_length - len(landmarks_sequence))
        elif len(landmarks_sequence) > self.sequence_length:
            # Truncate
            landmarks_sequence = landmarks_sequence[:self.sequence_length]
        
        # Flatten landmarks for each frame
        flattened_sequence = []
        for landmarks in landmarks_sequence:
            # Convert to numpy array if not already
            landmarks = np.array(landmarks)
            
            # Center the landmarks around the wrist
            wrist = landmarks[0]  # Wrist is the first landmark in MediaPipe
            centered = landmarks - wrist
            
            # Normalize for scale
            max_dist = np.max(np.abs(centered))
            if max_dist > 0:
                normalized = centered / max_dist
            else:
                normalized = centered
            
            # Flatten to 1D array
            flattened = normalized.flatten()
            flattened_sequence.append(flattened)
        
        return np.array(flattened_sequence)
    
    def create_model(self):
        """Create a new LSTM model for sign language recognition"""
        # Input shape: [sequence_length, features]
        input_shape = (self.sequence_length, self.num_landmarks * self.num_coords)
        num_classes = len(self.classes)
        
        model = Sequential([
            # First LSTM layer with bidirectional wrapper
            Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape),
            BatchNormalization(),
            Dropout(0.3),
            
            # Second LSTM layer
            Bidirectional(LSTM(128, return_sequences=True)),
            BatchNormalization(),
            Dropout(0.3),
            
            # Third LSTM layer
            LSTM(64),
            BatchNormalization(),
            Dropout(0.3),
            
            # Dense layers
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(32, activation='relu'),
            BatchNormalization(),
            
            # Output layer
            Dense(num_classes, activation='softmax')
        ])
        
        # Compile with Adam optimizer
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['categorical_accuracy']
        )
        
        self.model = model
        return model
    
    def prepare_data_from_directory(self, data_dir):
        """Load and preprocess training data from directory"""
        X = []
        y = []
        
        print(f"Loading data from {data_dir}")
        for class_idx, class_name in enumerate(self.classes):
            class_dir = os.path.join(data_dir, class_name)
            
            if not os.path.exists(class_dir):
                print(f"Warning: Directory for class {class_name} not found at {class_dir}")
                continue
            
            print(f"Processing class: {class_name}")
            files = [f for f in os.listdir(class_dir) if f.endswith('.npy')]
            print(f"Found {len(files)} sequences")
            
            for file_name in files:
                file_path = os.path.join(class_dir, file_name)
                sequence = np.load(file_path)
                
                # Preprocess landmarks
                processed_sequence = self.preprocess_landmarks(sequence)
                X.append(processed_sequence)
                y.append(class_idx)
        
        return np.array(X), np.array(y)
    
    def train(self, X, y, epochs=100, batch_size=16, validation_split=0.2):
        """Train the model with sign language data"""
        if self.model is None:
            self.create_model()
        
        print(f"Training model with {len(X)} sequences")
        print(f"X shape: {X.shape}, y shape: {y.shape}")
        
        # Convert labels to one-hot encoding
        y_categorical = tf.keras.utils.to_categorical(y, num_classes=len(self.classes))
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y_categorical, test_size=validation_split, random_state=42
        )
        
        # Callbacks
        checkpoint = ModelCheckpoint(
            self.model_path,
            monitor='val_categorical_accuracy',
            verbose=1,
            save_best_only=True,
            mode='max'
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=0.0001,
            verbose=1
        )
        
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=20,
            restore_best_weights=True,
            verbose=1
        )
        
        # Train the model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=[checkpoint, reduce_lr, early_stopping]
        )
        
        # Load the best model
        self.model = load_model(self.model_path)
        
        return history
    
    def predict(self, landmarks_sequence):
        """Predict sign from a sequence of hand landmarks"""
        if self.model is None:
            raise ValueError("Model not initialized. Create or load a model first.")
        
        if not landmarks_sequence:
            return "unknown", 0.0
        
        # Preprocess the landmarks
        try:
            processed_sequence = self.preprocess_landmarks(landmarks_sequence)
            
            # Add batch dimension
            X = np.expand_dims(processed_sequence, axis=0)
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            
            # Get class and confidence
            predicted_class_idx = np.argmax(prediction)
            confidence = prediction[predicted_class_idx]
            
            if confidence < 0.5:
                return "uncertain", float(confidence)
            
            return self.classes[predicted_class_idx], float(confidence)
        
        except Exception as e:
            print(f"Error in prediction: {e}")
            return "error", 0.0