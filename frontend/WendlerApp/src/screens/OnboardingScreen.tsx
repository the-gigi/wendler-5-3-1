import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { ApiService } from '../services/apiService';

interface OnboardingData {
  squat: string;
  bench: string;
  deadlift: string;
  overhead_press: string;
  unit: 'lbs' | 'kg';
  day1_movements: string[];
  day2_movements: string[];
}

const MOVEMENTS = [
  { key: 'squat', name: 'Back Squat' },
  { key: 'bench', name: 'Bench Press' },
  { key: 'deadlift', name: 'Deadlift' },
  { key: 'overhead_press', name: 'Press' }
];

const RECOMMENDED_SPLITS = [
  { 
    name: 'Upper/Lower Split',
    day1: ['squat', 'overhead_press'],
    day2: ['bench', 'deadlift']
  },
  {
    name: 'Push/Pull Split', 
    day1: ['squat', 'bench'],
    day2: ['deadlift', 'overhead_press']
  }
];

export const OnboardingScreen: React.FC = () => {
  const { refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<OnboardingData>({
    squat: '',
    bench: '',
    deadlift: '',
    overhead_press: '',
    unit: 'lbs',
    day1_movements: [],
    day2_movements: [],
  });

  const handleInputChange = (field: keyof OnboardingData, value: string | string[]) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const applyRecommendedSplit = (split: { day1: string[], day2: string[] }) => {
    setData(prev => ({
      ...prev,
      day1_movements: split.day1,
      day2_movements: split.day2
    }));
  };

  const toggleMovementForDay = (day: 'day1' | 'day2', movement: string) => {
    const dayKey = `${day}_movements` as keyof OnboardingData;
    const currentMovements = data[dayKey] as string[];
    
    if (currentMovements.includes(movement)) {
      // Remove movement
      const newMovements = currentMovements.filter(m => m !== movement);
      setData(prev => ({ ...prev, [dayKey]: newMovements }));
    } else if (currentMovements.length < 2) {
      // Add movement if less than 2
      const newMovements = [...currentMovements, movement];
      setData(prev => ({ ...prev, [dayKey]: newMovements }));
    }
  };

  const validateStep1 = (): boolean => {
    const { squat, bench, deadlift, overhead_press } = data;
    
    if (!squat || !bench || !deadlift || !overhead_press) {
      Alert.alert('Error', 'Please fill in all weight fields');
      return false;
    }

    const weights = [squat, bench, deadlift, overhead_press];
    for (const weight of weights) {
      const num = parseFloat(weight);
      if (isNaN(num) || num <= 0) {
        Alert.alert('Error', 'Please enter valid positive numbers for all weights');
        return false;
      }
    }

    return true;
  };

  const validateStep2 = (): boolean => {
    if (data.day1_movements.length !== 2) {
      Alert.alert('Error', 'Please select exactly 2 movements for Day 1');
      return false;
    }
    if (data.day2_movements.length !== 2) {
      Alert.alert('Error', 'Please select exactly 2 movements for Day 2');
      return false;
    }
    
    // Check if squat and deadlift are on same day (not recommended)
    const day1HasSquatAndDeadlift = data.day1_movements.includes('squat') && data.day1_movements.includes('deadlift');
    const day2HasSquatAndDeadlift = data.day2_movements.includes('squat') && data.day2_movements.includes('deadlift');
    
    if (day1HasSquatAndDeadlift || day2HasSquatAndDeadlift) {
      Alert.alert(
        'Warning', 
        'We recommend splitting back squat and deadlift between different days. Are you sure you want to continue?',
        [
          { text: 'Go Back', style: 'cancel' },
          { text: 'Continue', onPress: () => handleSubmit() }
        ]
      );
      return false;
    }
    
    return true;
  };

  const handleNextStep = () => {
    if (currentStep === 1) {
      if (validateStep1()) {
        setCurrentStep(2);
      }
    } else {
      handleSubmit();
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (currentStep === 2 && !validateStep2()) return;

    setLoading(true);
    try {
      const onboardingData = {
        squat: parseFloat(data.squat),
        bench: parseFloat(data.bench),
        deadlift: parseFloat(data.deadlift),
        overhead_press: parseFloat(data.overhead_press),
        unit: data.unit,
        day1_movements: data.day1_movements,
        day2_movements: data.day2_movements,
      };

      await ApiService.completeOnboarding(onboardingData);
      await refreshUser(); // Refresh user data to update onboarded status
    } catch (error) {
      console.error('Onboarding error:', error);
      Alert.alert('Error', 'Failed to save your workout setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <>
      <View style={styles.headerContainer}>
        <Text style={styles.title}>Welcome to Wendler 5-3-1!</Text>
        <Text style={styles.subtitle}>
          Let's get started by entering your current 1RM (one rep max) for each of the four main lifts.
        </Text>
        <Text style={styles.description}>
          If you don't know your exact 1RM, enter a weight you can lift for 3-5 reps and we'll calculate it for you later.
        </Text>
      </View>

      <View style={styles.formContainer}>
        <View style={styles.unitSelector}>
          <TouchableOpacity
            style={[styles.unitButton, data.unit === 'lbs' && styles.unitButtonActive]}
            onPress={() => handleInputChange('unit', 'lbs')}
          >
            <Text style={[styles.unitButtonText, data.unit === 'lbs' && styles.unitButtonTextActive]}>
              lbs
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.unitButton, data.unit === 'kg' && styles.unitButtonActive]}
            onPress={() => handleInputChange('unit', 'kg')}
          >
            <Text style={[styles.unitButtonText, data.unit === 'kg' && styles.unitButtonTextActive]}>
              kg
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Back Squat</Text>
          <TextInput
            style={styles.input}
            value={data.squat}
            onChangeText={(value) => handleInputChange('squat', value)}
            placeholder={`Enter back squat 1RM in ${data.unit}`}
            placeholderTextColor="#999"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Bench Press</Text>
          <TextInput
            style={styles.input}
            value={data.bench}
            onChangeText={(value) => handleInputChange('bench', value)}
            placeholder={`Enter bench press 1RM in ${data.unit}`}
            placeholderTextColor="#999"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Deadlift</Text>
          <TextInput
            style={styles.input}
            value={data.deadlift}
            onChangeText={(value) => handleInputChange('deadlift', value)}
            placeholder={`Enter deadlift 1RM in ${data.unit}`}
            placeholderTextColor="#999"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Press</Text>
          <TextInput
            style={styles.input}
            value={data.overhead_press}
            onChangeText={(value) => handleInputChange('overhead_press', value)}
            placeholder={`Enter press 1RM in ${data.unit}`}
            placeholderTextColor="#999"
            keyboardType="numeric"
          />
        </View>
      </View>
    </>
  );

  const renderStep2 = () => (
    <>
      <View style={styles.headerContainer}>
        <Text style={styles.title}>Choose Your Schedule</Text>
        <Text style={styles.subtitle}>
          Select 2 movements for each workout day. We recommend splitting back squat and deadlift between different days.
        </Text>
      </View>

      <View style={styles.formContainer}>
        <Text style={styles.sectionTitle}>Recommended Splits</Text>
        {RECOMMENDED_SPLITS.map((split, index) => (
          <TouchableOpacity
            key={index}
            style={styles.recommendedSplitButton}
            onPress={() => applyRecommendedSplit(split)}
          >
            <Text style={styles.recommendedSplitTitle}>{split.name}</Text>
            <Text style={styles.recommendedSplitText}>
              Day 1: {split.day1.map(m => MOVEMENTS.find(mv => mv.key === m)?.name).join(', ')}
            </Text>
            <Text style={styles.recommendedSplitText}>
              Day 2: {split.day2.map(m => MOVEMENTS.find(mv => mv.key === m)?.name).join(', ')}
            </Text>
          </TouchableOpacity>
        ))}

        <Text style={styles.sectionTitle}>Or Choose Manually</Text>
        
        <View style={styles.dayContainer}>
          <Text style={styles.dayTitle}>Day 1 ({data.day1_movements.length}/2)</Text>
          <View style={styles.movementGrid}>
            {MOVEMENTS.map((movement) => (
              <TouchableOpacity
                key={movement.key}
                style={[
                  styles.movementButton,
                  data.day1_movements.includes(movement.key) && styles.movementButtonSelected
                ]}
                onPress={() => toggleMovementForDay('day1', movement.key)}
              >
                <Text style={[
                  styles.movementButtonText,
                  data.day1_movements.includes(movement.key) && styles.movementButtonTextSelected
                ]}>
                  {movement.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.dayContainer}>
          <Text style={styles.dayTitle}>Day 2 ({data.day2_movements.length}/2)</Text>
          <View style={styles.movementGrid}>
            {MOVEMENTS.map((movement) => (
              <TouchableOpacity
                key={movement.key}
                style={[
                  styles.movementButton,
                  data.day2_movements.includes(movement.key) && styles.movementButtonSelected
                ]}
                onPress={() => toggleMovementForDay('day2', movement.key)}
              >
                <Text style={[
                  styles.movementButtonText,
                  data.day2_movements.includes(movement.key) && styles.movementButtonTextSelected
                ]}>
                  {movement.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>
    </>
  );

  return (
    <ScrollView style={styles.container}>
      {currentStep === 1 ? renderStep1() : renderStep2()}
      
      <View style={styles.navigationContainer}>
        {currentStep > 1 && (
          <TouchableOpacity style={styles.backButton} onPress={handlePrevStep}>
            <Text style={styles.backButtonText}>Back</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[styles.nextButton, loading && styles.nextButtonDisabled]}
          onPress={handleNextStep}
          disabled={loading}
        >
          <Text style={styles.nextButtonText}>
            {loading ? 'Saving...' : currentStep === 1 ? 'Next' : 'Complete Setup'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  headerContainer: {
    padding: 20,
    paddingTop: 60,
    maxWidth: 500,
    alignSelf: 'center',
    width: '100%',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
    lineHeight: 22,
  },
  description: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    lineHeight: 20,
  },
  formContainer: {
    padding: 20,
    maxWidth: 400,
    alignSelf: 'center',
    width: '100%',
  },
  unitSelector: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 30,
    backgroundColor: '#e0e0e0',
    borderRadius: 8,
    padding: 4,
  },
  unitButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  unitButtonActive: {
    backgroundColor: '#4285F4',
  },
  unitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  unitButtonTextActive: {
    color: 'white',
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    backgroundColor: 'white',
  },
  submitButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  
  // Step 2 styles
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  recommendedSplitButton: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  recommendedSplitTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  recommendedSplitText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  dayContainer: {
    marginBottom: 24,
  },
  dayTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  movementGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 8,
  },
  movementButton: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    width: '48%',
    alignItems: 'center',
  },
  movementButtonSelected: {
    borderColor: '#4285F4',
    backgroundColor: '#f0f7ff',
  },
  movementButtonText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  movementButtonTextSelected: {
    color: '#4285F4',
    fontWeight: '600',
  },
  
  // Navigation styles
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: 400,
    alignSelf: 'center',
    width: '100%',
    paddingHorizontal: 20,
    paddingBottom: 40,
    paddingTop: 20,
  },
  backButton: {
    backgroundColor: '#f0f0f0',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 8,
    alignItems: 'center',
    minWidth: 100,
  },
  backButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  nextButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 8,
    alignItems: 'center',
    flex: 1,
    marginLeft: 12,
  },
  nextButtonDisabled: {
    backgroundColor: '#ccc',
  },
  nextButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});