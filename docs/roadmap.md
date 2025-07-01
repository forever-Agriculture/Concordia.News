# docs/roadmap.md

# Project Roadmap

## Completed ✅
- Switch from Kyiv time to UTC for consistency
- Implement separate log files for different components
- Add health check endpoint
- Schedule data collection every hour (Revised)
- Schedule data analysis once per day at 00:00 UTC
- Add resource monitoring for containers
- Add terms of service and privacy policy links
- Optimize SQLite db for high load
- Deploy to Hetzner (CX22/CPX21)
- Fix scheduler script base-10 interpretation
- Implement dark mode interface
- Set up SSL/TLS with Let's Encrypt
- Configure Nginx reverse proxy
- Set up basic security measures
- Container restart schedule at 22:30 UTC
- Basic security configuration with Nginx
- SSL/TLS with Let's Encrypt
- Fix scheduler script base-10 interpretation
- Optimize scheduler script timing and reliability (v2)
- **Adjust analysis schedule (to 23:30 UTC) for DeepSeek API off-peak discounts**

## In Progress ��
- Optimize article collection timing and reliability
- Improve error handling and logging
- Enhance monitoring and alerting system
- Add automated health checks and notifications

## Short-term Goals (Next 2-4 Weeks) 📅
1. **Performance & Reliability**
   # Updated Redis caching item with rationale
   - Implement Redis caching for frequently accessed API queries (e.g., media sources) to improve performance and reduce DB load. (Decision: Prioritize caching before considering Celery for task queueing).
   - Implement database backup system
   - Add automated database optimization (VACUUM is currently manual/part of maintenance script)
   - Optimize memory usage monitoring

2. **Critical Security** (Only Essential Items)
   - Configure basic firewall rules (UFW)
   - Disable password authentication for SSH (if not already done)
   - Regular security patches for critical vulnerabilities

3. **Monitoring Improvements**
   - Set up detailed resource usage tracking (beyond current logs)
   - Implement automated alert system
   - Create dashboard for system metrics (e.g., using Grafana)
   - Add performance monitoring (e.g., API response times)

## Medium-term Goals (2-3 Months) 🎯
1. **Feature Additions**
   - Implement API rate limiting
   - Create API documentation (e.g., Swagger/OpenAPI)
   - Implement article categorization improvements

2. **UI/UX Improvements**
   - Add interactive data visualizations (e.g., D3.js, Chart.js)
   - Implement advanced filtering options (e.g., by date, bias score range)
   - Create mobile-responsive design
   - Add source comparison tools

3. **Data Analysis**
   - Enhance AI analysis capabilities (e.g., refine prompts, explore other models)
   - Add historical trend analysis (visualize bias/sentiment over time)
   - Implement source credibility scoring (experimental)
   - Add multi-language support (initial planning)

## Long-term Vision (6+ Months) 🔭
1. **Platform Growth**
   - Launch paid API access
   - Add more news sources (incl. non-English)
   - Implement real-time analysis (potentially using websockets or streaming)
   - Create premium features (e.g., custom dashboards, advanced reports)

2. **Infrastructure**
   # Added potential Celery consideration here
   - Consider migration to PostgreSQL for scaling (only if SQLite limitations are hit)
   - Implement horizontal scaling capability for API and potentially workers (if Celery is adopted)
   - Set up CDN for static assets
   - Add geographic redundancy (multiple server locations)

3. **Analytics & Research**
   - Develop advanced bias detection models
   - Create research partnership program
   - Implement machine learning improvements (e.g., topic modeling)
   - Add custom analysis tools for users

## Monitoring & Maintenance 🔧
- Daily database health checks (automated)
- Weekly security audits (automated/manual checks)
- Monthly performance reviews
- Quarterly infrastructure assessment

## Future Considerations 💭
- Potential cloud provider migration (AWS, GCP, Azure)
- Advanced AI/ML implementation (e.g., custom models)
- Mobile app development (iOS/Android)
- Academic research partnerships
- Integration with fact-checking platforms

## Notes
- All dates and timelines are flexible
- Priorities may shift based on user feedback and operational needs
- Resource allocation will be reviewed regularly
- Security remains a top priority throughout

