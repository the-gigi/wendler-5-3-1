import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, Alert, TextInput, Modal, Animated } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { ApiService } from '../services/apiService';

interface SetData {
  percentage: number;
  reps: string | number;
  weight: number;
  completed_reps?: number;
  actual_weight?: number;
}

interface WorkoutData {
  id?: number;
  week: number;
  day: number;
  movements: string[];
  sets: Record<string, SetData[]>;
  status?: string;
  completed?: boolean;
}

interface CycleData {
  id: number;
  cycle_number: number;
  start_date: string;
  is_active: boolean;
  training_maxes: Record<string, number>;
  workouts: WorkoutData[];
  week_dates?: Record<number, {
    start: string;
    end: string;
    start_date: string;
    end_date: string;
  }>;
}


export const CyclesScreen: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [cycle, setCycle] = useState<CycleData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingWorkout, setEditingWorkout] = useState<WorkoutData | null>(null);
  const [workoutChanges, setWorkoutChanges] = useState<Record<string, SetData[]>>({});
  const [allCycles, setAllCycles] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isSavingWorkout, setIsSavingWorkout] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const fetchActiveCycle = async () => {
    try {
      setLoading(true);
      setError(null);
      const cycleData = await ApiService.getActiveCycle();
      setCycle(cycleData);
      
      // Also fetch cycle history
      const cycles = await ApiService.getCycles();
      setAllCycles(cycles);
    } catch (error) {
      console.error('Error fetching cycle:', error);
      setError('Failed to load current cycle');
    } finally {
      setLoading(false);
    }
  };

  const createNextCycle = async () => {
    try {
      setLoading(true);
      await ApiService.createNextCycle();
      Alert.alert('Success', 'Next cycle created successfully!');
      await fetchActiveCycle(); // Refresh data
    } catch (error) {
      console.error('Error creating next cycle:', error);
      Alert.alert('Error', 'Failed to create next cycle. Please try again.');
      setLoading(false);
    }
  };

  const formatMovementName = (movement: string): string => {
    if (movement === 'overhead_press') return 'Press';
    if (movement === 'squat') return 'Back Squat';
    return movement.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatWeight = (weight: number): string => {
    return weight % 1 === 0 ? weight.toString() : weight.toFixed(1);
  };

  const getWeekName = (week: number): string => {
    const weekNames = {
      1: '5+ Week',
      2: '3+ Week', 
      3: '5/3/1+ Week',
      4: 'Deload Week'
    };
    return weekNames[week as keyof typeof weekNames] || `Week ${week}`;
  };

  const getWeekDates = (week: number): string => {
    if (!cycle?.week_dates?.[week]) return '';
    const dates = cycle.week_dates[week];
    return `${dates.start} - ${dates.end}`;
  };

  const getCurrentWeek = (): number => {
    if (!cycle?.workouts) return 1;
    
    console.log('=== getCurrentWeek Debug ===');
    console.log('All workouts:', cycle.workouts.map(w => ({
      id: w.id,
      week: w.week,
      day: w.day,
      completed: w.completed
    })));
    
    // Find the first week that has incomplete workouts
    const weekCompletionStatus = new Map<number, { total: number, completed: number }>();
    
    cycle.workouts.forEach(workout => {
      const week = workout.week;
      if (!weekCompletionStatus.has(week)) {
        weekCompletionStatus.set(week, { total: 0, completed: 0 });
      }
      const status = weekCompletionStatus.get(week)!;
      status.total++;
      if (workout.completed) {
        status.completed++;
      }
    });
    
    console.log('Week completion status:', Object.fromEntries(weekCompletionStatus));
    
    for (let week = 1; week <= 4; week++) {
      const status = weekCompletionStatus.get(week);
      if (status && status.completed < status.total) {
        console.log(`Current week determined: ${week} (${status.completed}/${status.total} completed)`);
        return week;
      }
    }
    
    console.log('All weeks completed, returning week 4');
    return 4; // All weeks completed
  };

  const isAllWorkoutsCompleted = (): boolean => {
    if (!cycle?.workouts) return false;
    return cycle.workouts.every(workout => workout.completed);
  };

  const getWorkoutStatus = (workout: WorkoutData): 'completed' | 'in-progress' | 'not-started' | 'dnf' | 'skipped' => {
    return workout.status || 'not-started';
  };


  const getFirstNotStartedWorkout = (): WorkoutData | null => {
    if (!cycle?.workouts) return null;
    
    // Sort workouts by week, then day
    const sortedWorkouts = [...cycle.workouts].sort((a, b) => {
      if (a.week !== b.week) return a.week - b.week;
      return a.day - b.day;
    });
    
    console.log('=== getFirstNotStartedWorkout Debug ===');
    console.log('Sorted workouts:', sortedWorkouts.map(w => ({
      id: w.id,
      week: w.week,
      day: w.day,
      status: getWorkoutStatus(w)
    })));
    
    const firstNotStarted = sortedWorkouts.find(workout => getWorkoutStatus(workout) === 'not-started') || null;
    console.log('First not started workout:', firstNotStarted ? {
      id: firstNotStarted.id,
      week: firstNotStarted.week,
      day: firstNotStarted.day
    } : 'none');
    
    return firstNotStarted;
  };

  const updateWorkoutStatus = async (workoutId: number, newStatus: string) => {
    try {
      await ApiService.updateWorkoutStatus(workoutId, newStatus);
      await fetchActiveCycle(); // Refresh to show the change
    } catch (error) {
      console.error('Error updating workout status:', error);
      Alert.alert('Error', 'Failed to update workout status. Please try again.');
    }
  };

  const getWorkoutCardStyle = (workout: WorkoutData) => {
    const status = getWorkoutStatus(workout);
    const baseStyle = styles.workoutCard;
    
    switch (status) {
      case 'completed':
        return [baseStyle, styles.workoutCardCompleted];
      case 'in-progress':
        return [baseStyle, styles.workoutCardInProgress];
      case 'dnf':
        return [baseStyle, styles.workoutCardDNF];
      case 'skipped':
        return [baseStyle, styles.workoutCardSkipped];
      default:
        return baseStyle;
    }
  };

  const openWorkoutEditor = (workout: WorkoutData) => {
    setEditingWorkout(workout);
    setWorkoutChanges(JSON.parse(JSON.stringify(workout.sets))); // Deep copy
    setHasUnsavedChanges(false);
  };

  const cancelWorkoutEditor = () => {
    setEditingWorkout(null);
    setWorkoutChanges({});
    setHasUnsavedChanges(false);
  };

  const updateSetData = (movement: string, setIndex: number, field: 'actual_weight' | 'completed_reps', value: string) => {
    const numValue = parseFloat(value) || 0;
    setWorkoutChanges(prev => ({
      ...prev,
      [movement]: prev[movement].map((set, index) => 
        index === setIndex 
          ? { ...set, [field]: numValue }
          : set
      )
    }));
    setHasUnsavedChanges(true);
  };

  const saveWorkout = async () => {
    if (!editingWorkout?.id) {
      Alert.alert('Error', 'No workout selected to save');
      return;
    }
    
    try {
      setIsSavingWorkout(true);
      await ApiService.updateWorkoutSets(editingWorkout.id, workoutChanges);
      
      // Check if the FINAL set of each movement is completed
      const allMovementsCompleted = editingWorkout.movements.every(movement => {
        const sets = workoutChanges[movement] || [];
        if (sets.length === 0) return false;
        
        // Only check the last set (AMRAP set in Wendler 5-3-1)
        const finalSet = sets[sets.length - 1];
        return finalSet.completed_reps !== undefined && 
               finalSet.completed_reps !== null && 
               finalSet.completed_reps > 0;
      });
      
      if (allMovementsCompleted) {
        await ApiService.completeWorkout(editingWorkout.id);
      }
      
      await fetchActiveCycle(); // Refresh data
      setEditingWorkout(null);
      setWorkoutChanges({});
      setHasUnsavedChanges(false);
      
      Alert.alert('Success', 'Workout saved successfully!');
    } catch (error) {
      console.error('Error saving workout:', error);
      Alert.alert('Error', 'Failed to save workout. Please try again.');
    } finally {
      setIsSavingWorkout(false);
    }
  };

  const renderWorkout = (workout: WorkoutData, index: number) => (
    <TouchableOpacity 
      key={index} 
      style={getWorkoutCardStyle(workout)}
      onPress={() => openWorkoutEditor(workout)}
    >
      <View style={styles.workoutHeader}>
        <Text style={styles.workoutTitle}>
          {getWeekName(workout.week)} - Day {workout.day}
        </Text>
        <Text style={styles.workoutDates}>
          {getWeekDates(workout.week)}
        </Text>
        <Text style={styles.workoutMovements}>
          {workout.movements.map(formatMovementName).join(' • ')}
        </Text>
      </View>
      
      {workout.movements.map(movement => (
        <View key={movement} style={styles.movementSection}>
          <Text style={styles.movementName}>{formatMovementName(movement)}</Text>
          <View style={styles.setsContainer}>
            {workout.sets[movement]?.map((set, setIndex) => (
              <View key={setIndex} style={styles.setRow}>
                <Text style={styles.setNumber}>Set {setIndex + 1}</Text>
                <Text style={styles.setDetails}>
                  {formatWeight(set.actual_weight || set.weight)} lbs × {set.completed_reps || set.reps} ({set.percentage}%)
                </Text>
              </View>
            ))}
          </View>
        </View>
      ))}
      
      {(() => {
        const workoutStatus = getWorkoutStatus(workout);
        const firstNotStarted = getFirstNotStartedWorkout();
        const shouldShowStartButton = workoutStatus === 'not-started' && firstNotStarted?.id === workout.id;
        
        if (shouldShowStartButton) {
          return (
            <TouchableOpacity 
              style={styles.startButton}
              onPress={(e) => {
                e.stopPropagation();
                updateWorkoutStatus(workout.id!, 'in-progress');
              }}
            >
              <Text style={styles.startButtonText}>▶ Start Workout</Text>
            </TouchableOpacity>
          );
        } else if (workoutStatus === 'in-progress') {
          return (
            <View style={styles.statusDropdownContainer}>
              <Text style={styles.statusLabel}>Status:</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={workoutStatus}
                  style={styles.statusPicker}
                  onValueChange={(itemValue) => {
                    if (itemValue !== workoutStatus) {
                      updateWorkoutStatus(workout.id!, itemValue);
                    }
                  }}
                >
                  <Picker.Item label="In Progress" value="in-progress" />
                  <Picker.Item label="Completed" value="completed" />
                  <Picker.Item label="DNF (Did Not Finish)" value="dnf" />
                  <Picker.Item label="Skipped" value="skipped" />
                </Picker>
              </View>
            </View>
          );
        } else {
          return (
            <Text style={styles.tapToEdit}>Tap to {workout.completed ? 'view' : 'edit'}</Text>
          );
        }
      })()}
    </TouchableOpacity>
  );

  const renderTrainingMaxes = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Training Maxes</Text>
      <View style={styles.tmGrid}>
        {Object.entries(cycle?.training_maxes || {}).map(([movement, weight]) => (
          <View key={movement} style={styles.tmCard}>
            <Text style={styles.tmMovement}>{formatMovementName(movement)}</Text>
            <Text style={styles.tmWeight}>{formatWeight(weight)} lbs</Text>
          </View>
        ))}
      </View>
    </View>
  );

  useEffect(() => {
    fetchActiveCycle();
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4285F4" />
        <Text style={styles.loadingText}>Loading cycle...</Text>
      </View>
    );
  }

  if (error || !cycle) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>
          {error || 'No active cycle found'}
        </Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchActiveCycle}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const currentWeek = getCurrentWeek();
  const currentWeekWorkouts = cycle.workouts.filter(w => w.week === currentWeek);
  const allWorkouts = cycle.workouts.sort((a, b) => {
    if (a.week !== b.week) return a.week - b.week;
    return a.day - b.day;
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Cycle {cycle.cycle_number}</Text>
        <Text style={styles.subtitle}>Current: {getWeekName(currentWeek)}</Text>
      </View>

      {renderTrainingMaxes()}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>This Week's Workouts</Text>
        {currentWeekWorkouts.length > 0 ? (
          currentWeekWorkouts.map((workout, index) => renderWorkout(workout, index))
        ) : (
          <Text style={styles.noWorkoutsText}>All workouts completed this week!</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>All Workouts</Text>
        {allWorkouts.map((workout, index) => renderWorkout(workout, index))}
      </View>

      {isAllWorkoutsCompleted() && (
        <View style={styles.section}>
          <TouchableOpacity style={styles.nextCycleButton} onPress={createNextCycle}>
            <Text style={styles.nextCycleButtonText}>Start Next Cycle</Text>
          </TouchableOpacity>
          <Text style={styles.nextCycleInfo}>
            Training maxes will be increased: Upper body +5lbs, Lower body +10lbs
          </Text>
        </View>
      )}

      {allCycles.length > 1 && (
        <View style={styles.section}>
          <TouchableOpacity 
            style={styles.historyButton} 
            onPress={() => setShowHistory(!showHistory)}
          >
            <Text style={styles.historyButtonText}>
              {showHistory ? 'Hide' : 'Show'} Cycle History ({allCycles.length - 1} completed)
            </Text>
          </TouchableOpacity>
          
          {showHistory && (
            <View style={styles.historySection}>
              {allCycles
                .filter(c => !c.is_active)
                .sort((a, b) => b.cycle_number - a.cycle_number)
                .map((pastCycle) => (
                <View key={pastCycle.id} style={styles.historyCycleCard}>
                  <Text style={styles.historyCycleTitle}>
                    Cycle {pastCycle.cycle_number}
                  </Text>
                  <Text style={styles.historyCycleDate}>
                    {new Date(pastCycle.start_date).toLocaleDateString()}
                  </Text>
                  <View style={styles.historyTMGrid}>
                    {Object.entries(pastCycle.training_maxes).map(([movement, weight]) => (
                      <Text key={movement} style={styles.historyTMText}>
                        {formatMovementName(movement)}: {formatWeight(weight as number)} lbs
                      </Text>
                    ))}
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Workout Editor Modal */}
      <Modal
        visible={editingWorkout !== null}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {editingWorkout && `${getWeekName(editingWorkout.week)} - Day ${editingWorkout.day}`}
              {hasUnsavedChanges && ' *'}
            </Text>
          </View>
          
          <ScrollView style={styles.modalContent}>
            {editingWorkout?.movements.map(movement => (
              <View key={movement} style={styles.editMovementSection}>
                <Text style={styles.editMovementName}>{formatMovementName(movement)}</Text>
                {workoutChanges[movement]?.map((set, setIndex) => (
                  <View key={setIndex} style={styles.editSetRow}>
                    <Text style={styles.editSetNumber}>Set {setIndex + 1}</Text>
                    <Text style={styles.editSetTarget}>
                      Target: {formatWeight(set.weight)} lbs × {set.reps} ({set.percentage}%)
                    </Text>
                    
                    <View style={styles.editInputRow}>
                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Weight</Text>
                        <TextInput
                          style={styles.editInput}
                          value={set.actual_weight?.toString() || set.weight.toString()}
                          onChangeText={(value) => updateSetData(movement, setIndex, 'actual_weight', value)}
                          keyboardType="numeric"
                          placeholder={set.weight.toString()}
                          placeholderTextColor="#999"
                        />
                      </View>
                      
                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Reps</Text>
                        <TextInput
                          style={styles.editInput}
                          value={set.completed_reps?.toString() || ''}
                          onChangeText={(value) => updateSetData(movement, setIndex, 'completed_reps', value)}
                          keyboardType="numeric"
                          placeholder={set.reps.toString()}
                          placeholderTextColor="#999"
                        />
                      </View>
                    </View>
                  </View>
                ))}
              </View>
            ))}
          </ScrollView>
          
          <View style={styles.modalFooter}>
            <View style={styles.footerButtons}>
              <TouchableOpacity 
                style={styles.cancelButton} 
                onPress={cancelWorkoutEditor}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.saveButton, isSavingWorkout && styles.saveButtonDisabled]} 
                onPress={saveWorkout}
                disabled={isSavingWorkout}
              >
                <Text style={styles.saveButtonText}>
                  {isSavingWorkout ? 'Saving...' : 'Save'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    maxWidth: 600,
    alignSelf: 'center',
    width: '100%',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  
  // Training Maxes
  tmGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  tmCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    width: '48%',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  tmMovement: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  tmWeight: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4285F4',
  },
  
  // Workouts
  workoutCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  workoutCardCompleted: {
    backgroundColor: '#f0f8f0',
    borderColor: '#4caf50',
    borderWidth: 2,
  },
  workoutCardInProgress: {
    backgroundColor: '#fffbf0',
    borderColor: '#ff9800',
    borderWidth: 2,
  },
  workoutCardDNF: {
    backgroundColor: '#fff5f5',
    borderColor: '#f44336',
    borderWidth: 2,
  },
  workoutCardSkipped: {
    backgroundColor: '#f5f5f5',
    borderColor: '#9e9e9e',
    borderWidth: 2,
  },
  tapToEdit: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  startButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  startButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  statusDropdownContainer: {
    paddingTop: 12,
    paddingHorizontal: 4,
  },
  statusLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  pickerContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#ddd',
    overflow: 'hidden',
  },
  statusPicker: {
    height: 40,
    fontSize: 14,
    color: '#333',
  },
  workoutHeader: {
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    paddingBottom: 12,
    marginBottom: 16,
  },
  workoutTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  workoutDates: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  workoutMovements: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  movementSection: {
    marginBottom: 16,
  },
  movementName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  setsContainer: {
    marginLeft: 12,
  },
  setRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
    position: 'relative',
  },
  setNumber: {
    fontSize: 14,
    color: '#666',
  },
  setDetails: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  
  // States
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  noWorkoutsText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // Next Cycle
  nextCycleButton: {
    backgroundColor: '#34A853',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  nextCycleButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  nextCycleInfo: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
  
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
    maxWidth: 600,
    alignSelf: 'center',
    width: '100%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  modalClose: {
    fontSize: 16,
    color: '#4285F4',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalFooter: {
    padding: 20,
    paddingBottom: 40,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  
  // Edit workout styles
  editMovementSection: {
    marginBottom: 32,
  },
  editMovementName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  editSetRow: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  editSetNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  editSetTarget: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  editInputRow: {
    flexDirection: 'row',
    gap: 16,
  },
  inputGroup: {
    flex: 1,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
  },
  editInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: 'white',
    color: '#333',
  },
  footerButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    backgroundColor: '#6c757d',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    flex: 1,
  },
  cancelButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  saveButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    flex: 1,
  },
  saveButtonDisabled: {
    backgroundColor: '#ccc',
  },
  saveButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  
  // History styles
  historyButton: {
    backgroundColor: '#f8f9fa',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    marginBottom: 16,
  },
  historyButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '500',
  },
  historySection: {
    marginTop: 8,
  },
  historyCycleCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  historyCycleTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  historyCycleDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 12,
  },
  historyTMGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  historyTMText: {
    fontSize: 12,
    color: '#666',
    backgroundColor: 'white',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
});