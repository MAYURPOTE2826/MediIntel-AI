from flask import Blueprint, jsonify, request, g
from app.trends.services import extract_and_compare_trends
from app.auth.security import require_auth
from . import trends_bp

@trends_bp.route('/compare', methods=['GET'])
@require_auth
def compare_reports():
    """
    Compare two medical reports and extract trends.
    Query parameters: report_id_1, report_id_2
    """
    report_id_1 = request.args.get('report_id_1')
    report_id_2 = request.args.get('report_id_2')
    
    if not report_id_1 or not report_id_2:
        return jsonify({"error": "Missing report_id_1 or report_id_2"}), 400
        
    try:
        # report_id_1 is older, report_id_2 is newer
        trends_data = extract_and_compare_trends(report_id_1, report_id_2)
        return jsonify(trends_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal server error during trend extraction"}), 500
