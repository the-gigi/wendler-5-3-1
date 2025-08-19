import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, TouchableOpacity, Modal, FlatList } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { ApiService, AdminStats, AdminUser, AdminCycle, AdminUserDetail } from '../services/apiService';

export const AdminScreen: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [cycles, setCycles] = useState<AdminCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUserList, setShowUserList] = useState(false);
  const [showCycleList, setShowCycleList] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUserDetail | null>(null);
  const [_selectedCycle, _setSelectedCycle] = useState<AdminCycle | null>(null);

  const isAdmin = user?.email === 'the.gigi@gmail.com';

  useEffect(() => {
    if (isAdmin) {
      loadAdminData();
    } else {
      setLoading(false);
    }
  }, [isAdmin]);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      
      // Load admin stats
      const statsResponse = await ApiService.getAdminStats();
      setStats(statsResponse);
      
      // Load users and cycles
      const [usersResponse, cyclesResponse] = await Promise.all([
        ApiService.getAdminUsers(),
        ApiService.getAdminCycles()
      ]);
      
      setUsers(usersResponse);
      setCycles(cyclesResponse);
    } catch (error) {
      console.error('Error loading admin data:', error);
      Alert.alert('Error', 'Failed to load admin data. Make sure you have admin access.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewUser = async (userId: number) => {
    try {
      const userDetail = await ApiService.getAdminUserDetail(userId);
      setSelectedUser(userDetail);
    } catch (error) {
      Alert.alert('Error', 'Failed to load user details');
    }
  };

  const handleDeleteUser = async (userId: number, userName: string) => {
    if (userId === user?.id) {
      Alert.alert('Error', 'Cannot delete your own account');
      return;
    }

    Alert.alert(
      'Delete User',
      `Are you sure you want to delete ${userName} and ALL associated data? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await ApiService.deleteAdminUser(userId);
              Alert.alert('Success', 'User deleted successfully');
              loadAdminData(); // Refresh data
            } catch (error) {
              Alert.alert('Error', 'Failed to delete user');
            }
          }
        }
      ]
    );
  };

  const handleDeleteCycle = async (cycleId: number, cycleNumber: number) => {
    Alert.alert(
      'Delete Cycle',
      `Are you sure you want to delete Cycle ${cycleNumber} and ALL associated workouts? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await ApiService.deleteAdminCycle(cycleId);
              Alert.alert('Success', 'Cycle deleted successfully');
              loadAdminData(); // Refresh data
            } catch (error) {
              Alert.alert('Error', 'Failed to delete cycle');
            }
          }
        }
      ]
    );
  };

  const renderUserItem = ({ item }: { item: AdminUser }) => (
    <View style={styles.listItem}>
      <View style={styles.listItemContent}>
        <Text style={styles.listItemTitle}>{item.name}</Text>
        <Text style={styles.listItemSubtitle}>{item.email}</Text>
        <Text style={styles.listItemDetail}>
          {item.provider} • {item.is_onboarded ? 'Onboarded' : 'Not onboarded'}
        </Text>
      </View>
      <View style={styles.listItemActions}>
        <TouchableOpacity
          style={styles.viewButton}
          onPress={() => handleViewUser(item.id)}
        >
          <Text style={styles.viewButtonText}>View</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDeleteUser(item.id, item.name)}
        >
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderCycleItem = ({ item }: { item: AdminCycle }) => (
    <View style={styles.listItem}>
      <View style={styles.listItemContent}>
        <Text style={styles.listItemTitle}>Cycle {item.cycle_number}</Text>
        <Text style={styles.listItemSubtitle}>{item.user?.name} ({item.user?.email})</Text>
        <Text style={styles.listItemDetail}>
          {item.is_active ? 'Active' : 'Inactive'} • {new Date(item.start_date).toLocaleDateString()}
        </Text>
      </View>
      <View style={styles.listItemActions}>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDeleteCycle(item.id, item.cycle_number)}
        >
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (!isAdmin) {
    return (
      <View style={styles.unauthorizedContainer}>
        <Text style={styles.unauthorizedTitle}>Access Denied</Text>
        <Text style={styles.unauthorizedText}>
          You don't have permission to access the admin interface.
        </Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading admin data...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Admin Dashboard</Text>
      <Text style={styles.subtitle}>Welcome, {user?.name}</Text>

      {/* Stats Overview */}
      <View style={styles.statsContainer}>
        <Text style={styles.sectionTitle}>Statistics</Text>
        {stats && (
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{stats.totalUsers}</Text>
              <Text style={styles.statLabel}>Total Users</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{stats.activeCycles}</Text>
              <Text style={styles.statLabel}>Active Cycles</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{stats.totalCycles}</Text>
              <Text style={styles.statLabel}>Total Cycles</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{stats.lastWeekNewUsers}</Text>
              <Text style={styles.statLabel}>New Users (7d)</Text>
            </View>
          </View>
        )}
      </View>

      {/* Management Actions */}
      <View style={styles.actionsContainer}>
        <Text style={styles.sectionTitle}>Data Management</Text>
        <TouchableOpacity style={styles.actionButton} onPress={() => setShowUserList(true)}>
          <Text style={styles.actionButtonText}>Manage Users ({users.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={() => setShowCycleList(true)}>
          <Text style={styles.actionButtonText}>Manage Cycles ({cycles.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={loadAdminData}>
          <Text style={styles.actionButtonText}>Refresh Data</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionButton, styles.secondaryButton]} 
          onPress={async () => {
            try {
              const result = await ApiService.exportAdminData('users');
              Alert.alert('Export Started', result.message);
            } catch (error) {
              Alert.alert('Export Error', 'Failed to start export. Please try again.');
            }
          }}
        >
          <Text style={styles.actionButtonText}>Export User Data</Text>
        </TouchableOpacity>
      </View>

      {/* User List Modal */}
      <Modal
        visible={showUserList}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowUserList(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Manage Users</Text>
              <TouchableOpacity onPress={() => setShowUserList(false)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={users}
              renderItem={renderUserItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.modalList}
            />
          </View>
        </View>
      </Modal>

      {/* Cycle List Modal */}
      <Modal
        visible={showCycleList}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowCycleList(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Manage Cycles</Text>
              <TouchableOpacity onPress={() => setShowCycleList(false)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={cycles}
              renderItem={renderCycleItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.modalList}
            />
          </View>
        </View>
      </Modal>

      {/* User Detail Modal */}
      <Modal
        visible={!!selectedUser}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setSelectedUser(null)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>User Details</Text>
              <TouchableOpacity onPress={() => setSelectedUser(null)}>
                <Text style={styles.closeButton}>✕</Text>
              </TouchableOpacity>
            </View>
            {selectedUser && (
              <ScrollView style={styles.modalList}>
                <View style={styles.detailSection}>
                  <Text style={styles.detailTitle}>User Information</Text>
                  <Text style={styles.detailText}>Name: {selectedUser.name}</Text>
                  <Text style={styles.detailText}>Email: {selectedUser.email}</Text>
                  <Text style={styles.detailText}>Provider: {selectedUser.provider}</Text>
                  <Text style={styles.detailText}>Onboarded: {selectedUser.is_onboarded ? 'Yes' : 'No'}</Text>
                  <Text style={styles.detailText}>Created: {new Date(selectedUser.created_at).toLocaleDateString()}</Text>
                </View>
                
                <View style={styles.detailSection}>
                  <Text style={styles.detailTitle}>1RM Records ({selectedUser.one_rms?.length || 0})</Text>
                  {selectedUser.one_rms?.map((oneRM) => (
                    <Text key={oneRM.movement} style={styles.detailText}>
                      {oneRM.movement}: {oneRM.weight} {oneRM.unit}
                    </Text>
                  ))}
                </View>
                
                <View style={styles.detailSection}>
                  <Text style={styles.detailTitle}>Cycles ({selectedUser.cycles?.length || 0})</Text>
                  {selectedUser.cycles?.map((cycle) => (
                    <Text key={cycle.id} style={styles.detailText}>
                      Cycle {cycle.cycle_number}: {cycle.is_active ? 'Active' : 'Inactive'}
                    </Text>
                  ))}
                </View>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      <View style={styles.noteContainer}>
        <Text style={styles.noteText}>
          Note: This admin interface is only accessible to the.gigi@gmail.com
        </Text>
      </View>
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
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  statsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    width: '48%',
    marginBottom: 10,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  actionsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  secondaryButton: {
    backgroundColor: '#6c757d',
  },
  actionButtonText: {
    color: '#fff',
    textAlign: 'center',
    fontWeight: '600',
    fontSize: 16,
  },
  noteContainer: {
    backgroundColor: '#fff3cd',
    padding: 15,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
    marginBottom: 30,
  },
  noteText: {
    fontSize: 14,
    color: '#856404',
    fontStyle: 'italic',
  },
  unauthorizedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  unauthorizedTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#dc3545',
    marginBottom: 10,
  },
  unauthorizedText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    width: '90%',
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    fontSize: 24,
    color: '#666',
    fontWeight: 'bold',
  },
  modalList: {
    flex: 1,
  },
  listItem: {
    flexDirection: 'row',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  listItemContent: {
    flex: 1,
    marginRight: 10,
  },
  listItemTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  listItemSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  listItemDetail: {
    fontSize: 12,
    color: '#999',
  },
  listItemActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewButton: {
    backgroundColor: '#007AFF',
    padding: 8,
    borderRadius: 6,
    marginRight: 8,
  },
  viewButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  deleteButton: {
    backgroundColor: '#FF3B30',
    padding: 8,
    borderRadius: 6,
  },
  deleteButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  detailSection: {
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  detailTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  detailText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
});