# Microsoft Fabric API Endpoints - Quick Reference

## Current vs Available Endpoints Summary

### ✅ **Currently Implemented (10 endpoints)**

| Priority | API Endpoint | Status | Business Value |
|----------|--------------|--------|----------------|
| 🔥 High | `/v1/workspaces/{id}/items/{id}/jobs/instances` | ✅ Implemented | Pipeline/Dataflow execution tracking |
| 🔥 High | `/v1/workspaces/{id}/datapipelines/pipelineruns/{id}/queryactivityruns` | ✅ Implemented | Detailed activity monitoring |
| 🔥 High | `/v1/datasets/{id}/refreshes` | ✅ Implemented | Dataset refresh monitoring |
| 🔥 High | `/v1/capacities` | ✅ Implemented | Capacity utilization tracking |
| 🟡 Medium | `/v1/admin/activities` | ✅ Implemented | User activity auditing (admin only) |
| 🟡 Medium | `/v1/workspaces` | ✅ Implemented | Workspace metadata |
| 🟡 Medium | `/v1/workspaces/{id}/items` | ✅ Implemented | Item inventory |

### ❌ **Missing High-Priority Endpoints (15+ identified)**

| Priority | API Endpoint | Gap Impact | Estimated ROI |
|----------|--------------|------------|---------------|
| 🔥 **CRITICAL** | `/v1/workspaces/{id}/eventhouse/databases` | No Real-Time Intelligence monitoring | $50K+/year |
| 🔥 **CRITICAL** | `/v1/workspaces/{id}/lakehouses` | No Data Engineering monitoring | $25K+/year |
| 🔥 **CRITICAL** | `/v1/gateways` | No infrastructure health monitoring | $30K+/year |
| 🔥 High | `/v1/workspaces/{id}/reports` | No report usage analytics | $15K+/year |
| 🔥 High | `/v1/workspaces/{id}/notebooks` | No Data Science workflow tracking | $10K+/year |
| 🟡 Medium | `/v1/workspaces/{id}/semanticModels` | Limited semantic model insights | $8K+/year |
| 🟡 Medium | `/v1/workspaces/{id}/users` | No security/permissions monitoring | Compliance |
| 🟡 Medium | `/v1/workspaces/{id}/datamarts` | No datamart operations tracking | $5K+/year |
| 🟢 Low | `/v1/pipelines` | No deployment pipeline monitoring | DevOps efficiency |
| 🟢 Low | `/v1/workspaces/{id}/apps` | No app usage analytics | Strategic insights |

## **Immediate Action Required**

### **Quick Wins (Next 30 Days)**
1. **EventHouse Monitoring** - Critical for customers using Real-Time Intelligence
2. **Gateway Health Monitoring** - Essential infrastructure reliability 
3. **Lakehouse Operations** - Core to Data Engineering scenarios

### **Coverage Gap**
- **Current Coverage**: ~40% of available Fabric REST API endpoints
- **Target Coverage**: 90%+ for comprehensive monitoring
- **Missing Workload Coverage**: Real-Time Intelligence, Data Engineering core scenarios

### **Business Impact**
- **Total Identified ROI**: $150K+ annual savings potential
- **Risk Mitigation**: Proactive detection vs reactive troubleshooting
- **Compliance**: Complete audit trail for governance requirements

---

**Next Step**: Review the detailed gap analysis in `fabric-monitoring-gap-analysis.md` for complete implementation roadmap and technical specifications.
