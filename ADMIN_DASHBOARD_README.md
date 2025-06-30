# PDN Admin Dashboard

A secure, modular admin dashboard for managing PDN diagnosis data and user information.

## 🚀 Features

### ✅ **Authentication & Security**
- Password-only login (password: "Pdn")
- Session-based authentication
- Secure API endpoints with session validation

### ✅ **Data Management**
- View all user metadata in organized table
- Search functionality by email
- Refresh data from backend
- CSV export capability

### ✅ **User Data Display**
- Complete user information display
- Hebrew labels for all fields
- Responsive table design with scrolling

### ✅ **Interactive Features**
- **View Questionnaire**: Modal with formatted JSON data
- **Play Voice**: Audio player for voice recordings
- **Edit Diagnose**: Inline editing of PDN codes and comments

### ✅ **User Experience**
- Loading spinners for all operations
- Error handling with user-friendly messages
- Responsive design for all screen sizes
- Hebrew RTL support

## 📁 File Structure

```
app/
├── api/
│   ├── admin_dashboard_api.py    # Backend API endpoints
│   └── routes.py                 # Main routes (includes admin)
├── templates/
│   └── admin_dashboard.html      # Frontend dashboard
└── tests/
    └── test_admin_dashboard.py   # Test suite
```

## 🔧 API Endpoints

### Authentication
- `POST /admin/login` - Admin login
- `GET /admin/logout` - Admin logout

### Data Management
- `GET /admin/metadata` - Get all user metadata
- `GET /admin/metadata/csv` - Download metadata as CSV

### User Data
- `GET /admin/user/questionnaire/{email}` - Get user questionnaire
- `GET /admin/user/voice/{email}` - Get user voice recording
- `PUT /admin/user/diagnose/{email}` - Update user diagnose

### Page Access
- `GET /admin-dashboard` - Admin dashboard page

## 🎯 Data Fields (in order)

The dashboard displays the following fields in exact order:

1. **email** - User email address
2. **date** - Completion date
3. **pdn_code** - Original PDN code
4. **diagnose_pdn_code** - Diagnosed PDN code
5. **diagnose_comments** - Diagnosis comments
6. **first_name** - שם פרטי
7. **last_name** - שם משפחה
8. **phone** - טלפון
9. **native_language** - שפת אם
10. **gender** - מגדר
11. **education_level** - השכלה
12. **job_title** - תפקיד בעבודה
13. **birth_year** - שנת לידה
14. **Actions** - פעולות (Questionnaire, Voice, Edit)

## 🚀 Getting Started

### 1. **Access the Dashboard**
Navigate to: `https://your-domain.com/admin-dashboard`

### 2. **Login**
- Enter password: `Pdn`
- Click "כניסה" (Login)

### 3. **Use the Dashboard**
- **Search**: Use the search bar to filter by email
- **Refresh**: Click "🔄 רענן נתונים" to reload data
- **View Data**: Click action buttons for each user

## 🔍 Usage Guide

### **Viewing Questionnaire Data**
1. Click "שאלון" button on any user row
2. Modal opens with formatted questionnaire data
3. View user answers and completion details

### **Playing Voice Recordings**
1. Click "הקלטה" button on any user row
2. Modal opens with audio player
3. Play, pause, and control audio playback

### **Editing Diagnose Information**
1. Click "ערוך אבחון" button on any user row
2. Modal opens with editable fields
3. Update PDN code and comments
4. Click "שמור" to save changes

### **Searching Users**
1. Type email address in search bar
2. Table filters in real-time
3. Case-insensitive partial matching

## 🛡️ Security Features

- **Session Management**: Secure session tokens
- **Authentication Required**: All endpoints require valid session
- **Input Validation**: Sanitized user inputs
- **Error Handling**: Graceful error responses

## 🧪 Testing

Run the test suite:

```bash
python -m unittest tests/test_admin_dashboard.py
```

### Test Coverage
- ✅ Admin login/logout
- ✅ Data retrieval
- ✅ User questionnaire access
- ✅ Voice recording access
- ✅ Diagnose editing
- ✅ Session validation

## 🎨 UI/UX Features

### **Responsive Design**
- Mobile-friendly layout
- Scrollable table for large datasets
- Adaptive modal sizes

### **Loading States**
- Spinner for all async operations
- Disabled buttons during loading
- Progress feedback

### **Error Handling**
- User-friendly error messages
- Graceful fallbacks
- Network error recovery

### **Accessibility**
- Keyboard navigation support
- Screen reader friendly
- High contrast design

## 🔧 Configuration

### **Environment Variables**
- No additional configuration required
- Uses existing project settings

### **Customization**
- Modify `HARDCODED_CSV_DATA` in `admin_dashboard_api.py` for different data
- Update styling in `admin_dashboard.html`
- Extend API endpoints as needed

## 🚀 Deployment

The admin dashboard is automatically included with your main application:

1. **No additional setup required**
2. **Accessible at `/admin-dashboard`**
3. **Uses existing authentication system**
4. **Integrated with main app routing**

## 🔮 Future Enhancements

### **Planned Features**
- [ ] Real database integration
- [ ] Advanced filtering options
- [ ] Bulk operations
- [ ] Export to Excel
- [ ] User activity logs
- [ ] Admin user management

### **Optional Enhancements**
- [ ] Table sorting by columns
- [ ] Pagination for large datasets
- [ ] Real-time data updates
- [ ] Advanced search filters
- [ ] Data visualization charts

## 🐛 Troubleshooting

### **Common Issues**

1. **Login Fails**
   - Ensure password is exactly "Pdn"
   - Check browser console for errors

2. **Data Not Loading**
   - Verify session token is valid
   - Check network connectivity
   - Review server logs

3. **Modals Not Opening**
   - Ensure JavaScript is enabled
   - Check for console errors
   - Verify modal HTML structure

### **Debug Mode**
Enable debug logging in your application to see detailed API calls and responses.

## 📞 Support

For issues or questions:
1. Check the test suite for expected behavior
2. Review browser console for JavaScript errors
3. Check server logs for backend issues
4. Verify all files are properly deployed

---

**Note**: This admin dashboard is designed as a modular component that can be easily extended and customized for your specific needs. 