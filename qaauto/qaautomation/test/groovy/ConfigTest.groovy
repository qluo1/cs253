class ConfigTest extends GroovyTestCase {
    void testAssertions() {
        def fileReport = new File("qaHealthCheck/generateReport.py");
        assertTrue(fileReport.exists())
        assert fileReport.text.length() > 0

        def fileInstanceData = new File("qaHealthCheck/db_load_flow_instance_data.pl");
        assertTrue(fileInstanceData.exists())
        assert fileInstanceData.text.length() > 0
		
		def fileFetch = new File("e2efixIvcomSimulator/scripts/FetchMarketData.py");
        assertTrue(fileFetch.exists())
        assert fileFetch.text.length() > 0
		
		def fileCheck = new File("e2efixIvcomSimulator/scripts/CheckFieldValue.py");
        assertTrue(fileCheck.exists())
        assert fileCheck.text.length() > 0
    }
}