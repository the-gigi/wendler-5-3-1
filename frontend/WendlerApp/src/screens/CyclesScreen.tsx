import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, Alert, TextInput, Modal } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { ApiService } from '../services/apiService';

interface SetData {
  percentage: number;
  reps: string | number;
  weight: number;
  completed_reps?: number;
  actual_weight?: number;
  type?: 'warmup' | 'working';
  notes?: string;
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
  const [allCycles, setAllCycles] = useState<CycleData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingWorkout, setEditingWorkout] = useState<WorkoutData | null>(null);
  const [workoutChanges, setWorkoutChanges] = useState<Record<string, SetData[]>>({});
  const [isSavingWorkout, setIsSavingWorkout] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Cycle editing state
  const [editingCycleId, setEditingCycleId] = useState<number | null>(null);
  const [editingStartDate, setEditingStartDate] = useState<string>('');
  const [isSavingCycle, setIsSavingCycle] = useState(false);
  
  // Expansion states
  const [expandedCycles, setExpandedCycles] = useState<Set<number>>(new Set());
  const [expandedWorkouts, setExpandedWorkouts] = useState<Set<string>>(new Set());
  const [loadingCycles, setLoadingCycles] = useState<Set<number>>(new Set());

  const fetchCycles = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch both active cycle and all cycles
      const [activeCycleData, allCyclesData] = await Promise.all([
        ApiService.getActiveCycle(),
        ApiService.getCycles()
      ]);
      
      // Ensure we have valid data
      if (!Array.isArray(allCyclesData)) {
        throw new Error('Invalid cycles data received');
      }
      
      // Set all cycles, making sure active cycle is included with full data
      const cycles = allCyclesData.map((cycle: CycleData) => 
        cycle.is_active ? { ...cycle, ...activeCycleData } : cycle
      );
      
      // Ensure all cycles have workouts array
      const cyclesWithWorkouts = cycles.map(cycle => ({
        ...cycle,
        workouts: cycle.workouts || []
      }));
      
      setAllCycles(cyclesWithWorkouts.sort((a, b) => b.cycle_number - a.cycle_number));
      
      // Auto-expand active cycle
      const activeCycle = cyclesWithWorkouts.find(c => c.is_active);
      if (activeCycle) {
        setExpandedCycles(new Set([activeCycle.id]));
        
        // Auto-expand active workout
        const activeWorkout = getActiveWorkout(activeCycle);
        if (activeWorkout) {
          setExpandedWorkouts(new Set([getWorkoutKey(activeWorkout, activeCycle.id)]));
        }
      }
    } catch (err) {
      console.error('Error fetching cycles:', err);
      setError('Failed to load cycles');
    } finally {
      setLoading(false);
    }
  };

  const getActiveWorkout = (cycle: CycleData): WorkoutData | null => {
    if (!cycle?.workouts) return null;
    
    // Find first in-progress workout
    const inProgress = cycle.workouts.find(w => getWorkoutStatus(w) === 'in-progress');
    if (inProgress) return inProgress;
    
    // Find first not-started workout
    const sortedWorkouts = [...cycle.workouts].sort((a, b) => {
      if (a.week !== b.week) return a.week - b.week;
      return a.day - b.day;
    });
    
    return sortedWorkouts.find(w => getWorkoutStatus(w) === 'not-started') || null;
  };

  const getWorkoutKey = (workout: WorkoutData, cycleId: number): string => {
    return `${cycleId}-${workout.week}-${workout.day}`;
  };

  const toggleCycleExpansion = async (cycleId: number) => {
    setExpandedCycles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cycleId)) {
        newSet.delete(cycleId);
        // Also collapse all workouts in this cycle
        setExpandedWorkouts(prevWorkouts => {
          const newWorkoutSet = new Set(prevWorkouts);
          const cycle = allCycles.find(c => c.id === cycleId);
          if (cycle?.workouts) {
            cycle.workouts.forEach(workout => {
              newWorkoutSet.delete(getWorkoutKey(workout, cycleId));
            });
          }
          return newWorkoutSet;
        });
      } else {
        newSet.add(cycleId);
        
        // Fetch full cycle data with workouts if not already loaded
        const cycle = allCycles.find(c => c.id === cycleId);
        if (cycle && (!cycle.workouts || cycle.workouts.length === 0)) {
          fetchCycleWorkouts(cycleId);
        }
      }
      return newSet;
    });
  };

  const fetchCycleWorkouts = async (cycleId: number) => {
    try {
      setLoadingCycles(prev => new Set(prev).add(cycleId));
      const fullCycleData = await ApiService.getCycle(cycleId);
      
      // Update the cycle in our state with the full data
      setAllCycles(prev => prev.map(cycle => 
        cycle.id === cycleId ? fullCycleData : cycle
      ));
    } catch (err) {
      console.error('Error fetching cycle workouts:', err);
      // Don't show an alert for this, just log it
    } finally {
      setLoadingCycles(prev => {
        const newSet = new Set(prev);
        newSet.delete(cycleId);
        return newSet;
      });
    }
  };

  const toggleWorkoutExpansion = (workout: WorkoutData, cycleId: number) => {
    const key = getWorkoutKey(workout, cycleId);
    setExpandedWorkouts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const createNextCycle = async () => {
    try {
      setLoading(true);
      await ApiService.createNextCycle();
      Alert.alert('Success', 'Next cycle created successfully!');
      await fetchCycles(); // Refresh data
    } catch (err) {
      console.error('Error creating next cycle:', err);
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

  const getWeekDates = (week: number, cycle: CycleData): string => {
    if (!cycle?.week_dates?.[week]) return '';
    const dates = cycle.week_dates[week];
    return `${dates.start} - ${dates.end}`;
  };

  const getWorkoutStatus = (workout: WorkoutData): 'completed' | 'in-progress' | 'not-started' | 'dnf' | 'skipped' => {
    return workout.status || 'not-started';
  };

  const isAllWorkoutsCompleted = (cycle: CycleData): boolean => {
    if (!cycle?.workouts) return false;
    return cycle.workouts.every(workout => {
      const status = getWorkoutStatus(workout);
      return status === 'completed' || status === 'dnf' || status === 'skipped';
    });
  };

  const hasInProgressWorkout = (cycle: CycleData): boolean => {
    if (!cycle?.workouts) return false;
    return cycle.workouts.some(workout => getWorkoutStatus(workout) === 'in-progress');
  };

  const getFirstNotStartedWorkout = (cycle: CycleData): WorkoutData | null => {
    if (!cycle?.workouts) return null;
    
    const sortedWorkouts = [...cycle.workouts].sort((a, b) => {
      if (a.week !== b.week) return a.week - b.week;
      return a.day - b.day;
    });
    
    return sortedWorkouts.find(workout => getWorkoutStatus(workout) === 'not-started') || null;
  };

  const updateWorkoutStatus = async (workoutId: number, newStatus: string) => {
    try {
      await ApiService.updateWorkoutStatus(workoutId, newStatus);
      await fetchCycles(); // Refresh to show the change
    } catch (err) {
      console.error('Error updating workout status:', err);
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

  const startEditingCycle = (cycle: CycleData) => {
    setEditingCycleId(cycle.id);
    setEditingStartDate(cycle.start_date.split('T')[0]); // Convert to YYYY-MM-DD format
  };

  const cancelCycleEdit = () => {
    setEditingCycleId(null);
    setEditingStartDate('');
  };

  const saveCycleStartDate = async (cycleId: number) => {
    try {
      setIsSavingCycle(true);
      await ApiService.updateCycle(cycleId, {
        start_date: editingStartDate
      });
      
      await fetchCycles(); // Refresh data
      setEditingCycleId(null);
      setEditingStartDate('');
      
      Alert.alert('Success', 'Cycle start date updated!');
    } catch (err) {
      console.error('Error updating cycle:', err);
      Alert.alert('Error', 'Failed to update cycle start date.');
    } finally {
      setIsSavingCycle(false);
    }
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
      
      await fetchCycles(); // Refresh data
      setEditingWorkout(null);
      setWorkoutChanges({});
      setHasUnsavedChanges(false);
      
      Alert.alert('Success', 'Workout saved successfully!');
    } catch (err) {
      console.error('Error saving workout:', err);
      Alert.alert('Error', 'Failed to save workout. Please try again.');
    } finally {
      setIsSavingWorkout(false);
    }
  };

  const renderWorkoutSummary = (workout: WorkoutData, cycle: CycleData) => {
    const workoutStatus = getWorkoutStatus(workout);
    const firstNotStarted = getFirstNotStartedWorkout(cycle);
    const shouldShowStartButton = workoutStatus === 'not-started' && 
                                  firstNotStarted?.id === workout.id && 
                                  !hasInProgressWorkout(cycle);
    
    return (
      <TouchableOpacity 
        style={styles.workoutSummary}
        onPress={() => toggleWorkoutExpansion(workout, cycle.id)}
      >
        <View style={styles.workoutSummaryHeader}>
          <Text style={styles.workoutSummaryTitle}>
            {getWeekName(workout.week)} - Day {workout.day}
          </Text>
          <Text style={[styles.workoutStatus, getWorkoutStatusStyle(workoutStatus)]}>
            {workoutStatus.toUpperCase()}
          </Text>
        </View>
        <Text style={styles.workoutSummaryMovements}>
          {workout.movements.map(formatMovementName).join(' • ')}
        </Text>
        <Text style={styles.workoutSummaryDates}>
          {getWeekDates(workout.week, cycle)}
        </Text>
        
        {shouldShowStartButton && (
          <TouchableOpacity 
            style={styles.startButton}
            onPress={(e) => {
              e.stopPropagation();
              updateWorkoutStatus(workout.id!, 'in-progress');
            }}
          >
            <Text style={styles.startButtonText}>▶ Start Workout</Text>
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  };

  const renderWorkoutDetails = (workout: WorkoutData, _cycle: CycleData) => {
    const workoutStatus = getWorkoutStatus(workout);
    
    return (
      <View style={styles.workoutDetails}>
        <TouchableOpacity 
          style={getWorkoutCardStyle(workout)}
          onPress={() => openWorkoutEditor(workout)}
        >
          {workout.movements.map(movement => (
            <View key={movement} style={styles.movementSection}>
              <Text style={styles.movementName}>{formatMovementName(movement)}</Text>
              <View style={styles.setsContainer}>
                {workout.sets[movement]?.map((set, setIndex) => (
                  <View key={setIndex} style={[styles.setRow, set.type === 'warmup' && styles.warmupSetRow]}>
                    <Text style={[styles.setNumber, set.type === 'warmup' && styles.warmupSetNumber]}>
                      {set.type === 'warmup' ? 'Warmup Set' : 'Work Set'} {setIndex + 1}
                    </Text>
                    <Text style={[styles.setDetails, set.type === 'warmup' && styles.warmupSetDetails]}>
                      {formatWeight(set.actual_weight || set.weight)} lbs × {set.completed_reps || set.reps} ({set.percentage}%)
                      {set.notes && set.type !== 'warmup' && ` - ${set.notes}`}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          ))}
          
          <Text style={styles.tapToEdit}>Tap to {workout.completed ? 'view' : 'edit'}</Text>
        </TouchableOpacity>
        
        {workoutStatus === 'in-progress' && (
          <View style={styles.statusDropdownSidebar}>
            <Text style={styles.statusLabel}>Status</Text>
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
                <Picker.Item label="DNF" value="dnf" />
                <Picker.Item label="Skipped" value="skipped" />
              </Picker>
            </View>
          </View>
        )}

        {(workoutStatus === 'completed' || workoutStatus === 'dnf' || workoutStatus === 'skipped') && (
          <View style={styles.statusDropdownSidebar}>
            <Text style={styles.statusLabel}>Status</Text>
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
                <Picker.Item label={
                  workoutStatus === 'completed' ? 'Completed' :
                  workoutStatus === 'dnf' ? 'DNF' :
                  'Skipped'
                } value={workoutStatus} />
                <Picker.Item label="Reset to Not Started" value="not-started" />
              </Picker>
            </View>
          </View>
        )}
      </View>
    );
  };

  const getWorkoutStatusStyle = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: '#4caf50' };
      case 'in-progress':
        return { color: '#ff9800' };
      case 'dnf':
        return { color: '#e91e63' };
      case 'skipped':
        return { color: '#757575' };
      default:
        return { color: '#666' };
    }
  };

  const renderCycle = (cycle: CycleData) => {
    const isExpanded = expandedCycles.has(cycle.id);
    const sortedWorkouts = [...(cycle.workouts || [])].sort((a, b) => {
      if (a.week !== b.week) return a.week - b.week;
      return a.day - b.day;
    });
    
    // Group workouts by week for better organization
    const workoutsByWeek = sortedWorkouts.reduce((acc, workout) => {
      if (!acc[workout.week]) acc[workout.week] = [];
      acc[workout.week].push(workout);
      return acc;
    }, {} as Record<number, WorkoutData[]>);

    return (
      <View key={cycle.id} style={[styles.cycleCard, cycle.is_active && styles.activeCycleCard]}>
        <TouchableOpacity 
          style={styles.cycleHeader}
          onPress={() => toggleCycleExpansion(cycle.id)}
        >
          <View style={styles.cycleHeaderLeft}>
            <Text style={[styles.cycleTitle, cycle.is_active && styles.activeCycleTitle]}>
              Cycle {cycle.cycle_number}
              {cycle.is_active && ' (Current)'}
            </Text>
            {editingCycleId === cycle.id ? (
              <View style={styles.cycleDateEditContainer}>
                <TextInput
                  style={styles.cycleDateInput}
                  value={editingStartDate}
                  onChangeText={setEditingStartDate}
                  placeholder="YYYY-MM-DD"
                  placeholderTextColor="#999"
                  autoFocus
                />
                <View style={styles.editButtonsContainer}>
                  <TouchableOpacity 
                    style={styles.inlineSaveButton}
                    onPress={() => saveCycleStartDate(cycle.id)}
                    disabled={isSavingCycle}
                  >
                    <Text style={styles.inlineSaveButtonText}>
                      {isSavingCycle ? '...' : '✓'}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.inlineCancelButton}
                    onPress={cancelCycleEdit}
                  >
                    <Text style={styles.inlineCancelButtonText}>✕</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <TouchableOpacity 
                style={styles.cycleDateContainer}
                onPress={(e) => {
                  e.stopPropagation();
                  startEditingCycle(cycle);
                }}
              >
                <Text style={styles.cycleDate}>
                  Started {new Date(cycle.start_date).toLocaleDateString()}
                </Text>
                <Text style={styles.editHint}>✏️ Tap to edit</Text>
              </TouchableOpacity>
            )}
          </View>
          <Text style={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</Text>
        </TouchableOpacity>

        {isExpanded && (
          <View style={styles.cycleContent}>
            {/* Training Maxes */}
            <View style={styles.trainingMaxesSection}>
              <Text style={styles.sectionSubtitle}>Training Maxes</Text>
              <View style={styles.tmGrid}>
                {Object.entries(cycle.training_maxes || {}).map(([movement, weight]) => (
                  <View key={movement} style={styles.tmCard}>
                    <Text style={styles.tmMovement}>{formatMovementName(movement)}</Text>
                    <Text style={styles.tmWeight}>{formatWeight(weight)} lbs</Text>
                  </View>
                ))}
              </View>
            </View>

            {/* Workouts by Week */}
            {loadingCycles.has(cycle.id) ? (
              <View style={styles.loadingWorkoutsContainer}>
                <ActivityIndicator size="small" color="#4285F4" />
                <Text style={styles.loadingWorkoutsText}>Loading workouts...</Text>
              </View>
            ) : (
              Object.entries(workoutsByWeek).map(([week, workouts]) => (
                <View key={week} style={styles.weekSection}>
                  <Text style={styles.weekTitle}>{getWeekName(parseInt(week, 10))}</Text>
                  {workouts.map(workout => {
                    const workoutKey = getWorkoutKey(workout, cycle.id);
                    const isWorkoutExpanded = expandedWorkouts.has(workoutKey);
                    
                    return (
                      <View key={workoutKey} style={styles.workoutDrawer}>
                        {renderWorkoutSummary(workout, cycle)}
                        {isWorkoutExpanded && renderWorkoutDetails(workout, cycle)}
                      </View>
                    );
                  })}
                </View>
              ))
            )}

            {/* Next Cycle Button */}
            {cycle.is_active && isAllWorkoutsCompleted(cycle) && (
              <View style={styles.nextCycleSection}>
                <TouchableOpacity style={styles.nextCycleButton} onPress={createNextCycle}>
                  <Text style={styles.nextCycleButtonText}>Start Next Cycle</Text>
                </TouchableOpacity>
                <Text style={styles.nextCycleInfo}>
                  Training maxes will be increased: Upper body +5lbs, Lower body +10lbs
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  useEffect(() => {
    fetchCycles();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4285F4" />
        <Text style={styles.loadingText}>Loading cycles...</Text>
      </View>
    );
  }

  if (error || allCycles.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>
          {error || 'No cycles found'}
        </Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchCycles}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Training Cycles</Text>
        <Text style={styles.subtitle}>{allCycles.length} cycle{allCycles.length !== 1 ? 's' : ''}</Text>
      </View>

      <ScrollView style={styles.scrollContainer}>
        {allCycles.map(cycle => renderCycle(cycle))}
      </ScrollView>

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
                  <View key={setIndex} style={[styles.editSetRow, set.type === 'warmup' && styles.editWarmupSetRow]}>
                    <Text style={[styles.editSetNumber, set.type === 'warmup' && styles.editWarmupSetNumber]}>
                      {set.type === 'warmup' ? 'Warmup Set' : 'Work Set'} {setIndex + 1}
                    </Text>
                    <Text style={[styles.editSetTarget, set.type === 'warmup' && styles.editWarmupSetTarget]}>
                      Target: {formatWeight(set.weight)} lbs × {set.reps} ({set.percentage}%)
                      {set.notes && set.type !== 'warmup' && ` - ${set.notes}`}
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

    </View>
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
  scrollContainer: {
    flex: 1,
  },
  
  // Cycle Drawer Styles
  cycleCard: {
    backgroundColor: 'white',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    overflow: 'hidden',
  },
  activeCycleCard: {
    borderColor: '#4285F4',
    borderWidth: 2,
  },
  cycleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f9fa',
  },
  cycleHeaderLeft: {
    flex: 1,
  },
  cycleTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  activeCycleTitle: {
    color: '#4285F4',
  },
  cycleDateContainer: {
    marginTop: 4,
  },
  cycleDate: {
    fontSize: 14,
    color: '#666',
  },
  editHint: {
    fontSize: 10,
    color: '#4285F4',
    marginTop: 2,
    fontStyle: 'italic',
  },
  cycleDateEditContainer: {
    marginTop: 4,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cycleDateInput: {
    borderWidth: 1,
    borderColor: '#4285F4',
    borderRadius: 4,
    padding: 4,
    fontSize: 14,
    backgroundColor: 'white',
    minWidth: 100,
  },
  editButtonsContainer: {
    flexDirection: 'row',
    gap: 4,
  },
  inlineSaveButton: {
    backgroundColor: '#4285F4',
    borderRadius: 4,
    padding: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  inlineSaveButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  inlineCancelButton: {
    backgroundColor: '#6c757d',
    borderRadius: 4,
    padding: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  inlineCancelButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  expandIcon: {
    fontSize: 16,
    color: '#666',
    fontWeight: 'bold',
  },
  cycleContent: {
    padding: 20,
  },
  
  // Training Maxes
  trainingMaxesSection: {
    marginBottom: 24,
  },
  sectionSubtitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  tmGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  tmCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    width: '48%',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  tmMovement: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
    textAlign: 'center',
  },
  tmWeight: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4285F4',
  },
  
  // Week Sections
  weekSection: {
    marginBottom: 24,
  },
  weekTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
    paddingHorizontal: 8,
  },
  
  // Workout Drawers
  workoutDrawer: {
    marginBottom: 8,
  },
  workoutSummary: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  workoutSummaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  workoutSummaryTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  workoutStatus: {
    fontSize: 12,
    fontWeight: '600',
  },
  workoutSummaryMovements: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  workoutSummaryDates: {
    fontSize: 12,
    color: '#888',
  },
  workoutDetails: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 12,
  },
  
  // Workout Card Styles (same as before)
  workoutCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    flex: 1,
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
    backgroundColor: '#fce4ec',
    borderColor: '#e91e63',
    borderWidth: 2,
  },
  workoutCardSkipped: {
    backgroundColor: '#f5f5f5',
    borderColor: '#757575',
    borderWidth: 2,
  },
  movementSection: {
    marginBottom: 16,
  },
  movementName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  setsContainer: {
    marginLeft: 8,
  },
  setRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 2,
  },
  setNumber: {
    fontSize: 12,
    color: '#666',
  },
  setDetails: {
    fontSize: 12,
    fontWeight: '500',
    color: '#333',
  },
  warmupSetRow: {
    backgroundColor: '#f0f8ff',
  },
  warmupSetNumber: {
    color: '#4285F4',
    fontWeight: '600',
  },
  warmupSetDetails: {
    color: '#4285F4',
    fontStyle: 'italic',
  },
  tapToEdit: {
    fontSize: 10,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // Start Button
  startButton: {
    backgroundColor: '#4285F4',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 8,
  },
  startButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  
  // Status Dropdown
  statusDropdownSidebar: {
    width: 120,
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    alignSelf: 'flex-start',
  },
  statusLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    textAlign: 'center',
  },
  pickerContainer: {
    backgroundColor: '#4285F4',
    borderRadius: 4,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#4285F4',
  },
  statusPicker: {
    height: 30,
    fontSize: 11,
    color: 'white',
    backgroundColor: 'transparent',
  },
  
  // Next Cycle Section
  nextCycleSection: {
    marginTop: 24,
    paddingTop: 24,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  nextCycleButton: {
    backgroundColor: '#34A853',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  nextCycleButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  nextCycleInfo: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    lineHeight: 18,
  },
  
  // Loading/Error States
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  loadingWorkoutsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingWorkoutsText: {
    marginLeft: 12,
    fontSize: 14,
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
  
  // Modal styles (same as before)
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
  
  // Edit workout styles (same as before)
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
  editWarmupSetRow: {
    backgroundColor: '#f0f8ff',
    borderLeftWidth: 4,
    borderLeftColor: '#4285F4',
  },
  editWarmupSetNumber: {
    color: '#4285F4',
    fontWeight: '700',
  },
  editWarmupSetTarget: {
    color: '#4285F4',
    fontStyle: 'italic',
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
});