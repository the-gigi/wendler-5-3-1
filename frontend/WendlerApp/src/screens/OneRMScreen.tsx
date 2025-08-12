import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';

export const OneRMScreen: React.FC = () => {
  const { user } = useAuth();

  if (!user || !user.one_rms || user.one_rms.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.noDataText}>No 1RM records found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.oneRMSection}>
        <View style={styles.oneRMGrid}>
          {user.one_rms.map((oneRM) => (
            <View key={oneRM.movement} style={styles.oneRMCard}>
              <Text style={styles.movementName}>
                {oneRM.movement === 'overhead_press' ? 'Press' : 
                 oneRM.movement === 'squat' ? 'Back Squat' :
                 oneRM.movement.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Text>
              <Text style={styles.weightText}>{oneRM.weight} {oneRM.unit}</Text>
            </View>
          ))}
        </View>
      </View>
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
  oneRMSection: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  oneRMGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  oneRMCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    width: '48%',
    minWidth: 140,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  movementName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  weightText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4285F4',
  },
  noDataText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
});